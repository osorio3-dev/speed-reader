"""Main application window for RSVP speed reading."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from speedreader.engine import ReadingEngine
from speedreader.domain import SegmentKind
from speedreader.importers.clipboard import ClipboardImporter
from speedreader.orp import format_word_with_orp
from speedreader.importers.file import FileImporter, is_supported_file
from speedreader.importers.markdown import MarkdownImporter
from speedreader.settings import (
    MAX_FONT_SIZE,
    MAX_WPM,
    MIN_FONT_SIZE,
    MIN_WPM,
    SettingsStore,
)
from speedreader.paths import app_icon_path
from speedreader.profiles import READING_PROFILES
from speedreader.speech.base import SpeechBackend
from speedreader.speech.factory import create_speech_backend
from speedreader.speech.voices import (
    QT_VOICE_ID,
    list_installed_piper_voices,
    resolve_voice_selection,
    voice_label,
)
from speedreader.ui.shortcuts_dialog import ShortcutsDialog

IDLE_MESSAGE = "-- Speedreader --"
IDLE_HINT = "Pega, abre (Ctrl+O) o arrastra un .txt / .md"


class MainWindow(QMainWindow):
    """RSVP reader with paste, play/pause, and WPM controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Speedreader")
        self.resize(720, 360)
        self.setAcceptDrops(True)

        self._settings = SettingsStore()
        self._engine = ReadingEngine(
            wpm=self._settings.load_wpm(),
            profile_id=self._settings.load_reading_profile(),
        )
        self._normal_word_point_size = self._settings.load_font_size()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._phrase_timer = QTimer(self)
        self._phrase_timer.timeout.connect(self._on_phrase_visual_tick)
        self._phrase_word_offset = 0
        self._playing = False
        self._source_path: str | None = None
        self._source_kind: str | None = None
        self._voices_dir = self._settings.load_voices_dir()
        self._selected_voice_id = resolve_voice_selection(
            self._voices_dir,
            self._settings.load_tts_voice(),
        )
        self._speech = self._create_speech_backend()
        self._apply_speech_rate()
        self._tts_enabled = self._settings.load_tts_enabled()

        self._word_label = QLabel(IDLE_MESSAGE)
        self._word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_word_font_size(self._normal_word_point_size)

        self._status_label = QLabel(f"0 / 0 words · {self._engine.wpm} WPM")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setEnabled(False)
        self._progress_slider.valueChanged.connect(self._on_progress_changed)

        self._paste_button = QPushButton("Paste")
        self._paste_button.clicked.connect(self._paste_from_clipboard)

        self._open_button = QPushButton("Open")
        self._open_button.clicked.connect(self._open_file)

        self._play_button = QPushButton("Play")
        self._play_button.clicked.connect(self._toggle_playback)
        self._play_button.setEnabled(False)

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(self._reset_reading)
        self._reset_button.setEnabled(False)

        self._tts_button = QPushButton("TTS")
        self._tts_button.setCheckable(True)
        self._tts_button.setChecked(self._tts_enabled)
        self._tts_button.setToolTip(f"Speech: {self._speech.name}")
        self._tts_button.toggled.connect(self._on_tts_toggled)

        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(220)
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        self._refresh_voice_combo()

        self._wpm_slider = QSlider(Qt.Orientation.Horizontal)
        self._wpm_slider.setRange(MIN_WPM, MAX_WPM)
        self._wpm_slider.setValue(self._engine.wpm)
        self._wpm_slider.setTickInterval(100)
        self._wpm_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._wpm_slider.valueChanged.connect(self._on_wpm_changed)

        self._wpm_label = QLabel(f"{self._engine.wpm} WPM")

        self._profile_combo = QComboBox()
        for profile in READING_PROFILES.values():
            self._profile_combo.addItem(profile.label, profile.id)
        profile_index = self._profile_combo.findData(self._engine.profile_id)
        if profile_index >= 0:
            self._profile_combo.setCurrentIndex(profile_index)
        self._profile_combo.currentIndexChanged.connect(self._on_profile_changed)

        self._font_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_slider.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self._font_slider.setValue(self._normal_word_point_size)
        self._font_slider.setTickInterval(12)
        self._font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_slider.valueChanged.connect(self._on_font_size_changed)

        self._font_label = QLabel(f"{self._normal_word_point_size} pt")

        controls = QHBoxLayout()
        controls.addWidget(self._open_button)
        controls.addWidget(self._paste_button)
        controls.addWidget(self._play_button)
        controls.addWidget(self._reset_button)
        controls.addWidget(self._tts_button)
        controls.addWidget(self._voice_combo)
        controls.addStretch()

        tuning = QVBoxLayout()
        font_row = QHBoxLayout()
        font_row.addWidget(self._font_label)
        font_row.addWidget(self._font_slider)
        wpm_row = QHBoxLayout()
        wpm_row.addWidget(self._wpm_label)
        wpm_row.addWidget(self._wpm_slider)
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Perfil"))
        profile_row.addWidget(self._profile_combo)
        tuning.addLayout(font_row)
        tuning.addLayout(wpm_row)
        tuning.addLayout(profile_row)
        controls.addLayout(tuning)

        self._controls = QWidget()
        self._controls.setLayout(controls)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self._word_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_slider)
        layout.addStretch()
        layout.addWidget(self._controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        icon_path = app_icon_path()
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        self._setup_shortcuts()
        self._restore_reading_session()
        if self._engine.is_empty:
            self._show_idle_message()

    def _show_idle_message(self) -> None:
        self._set_plain_message(IDLE_MESSAGE)
        self._update_status()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._settings.save_wpm(self._engine.wpm)
        self._settings.save_font_size(self._normal_word_point_size)
        self._settings.save_tts_enabled(self._tts_enabled)
        self._settings.save_tts_voice(self._selected_voice_id)
        self._settings.save_reading_profile(self._engine.profile_id)
        self._persist_reading_session()
        self._speech.stop()
        super().closeEvent(event)

    def _create_speech_backend(self) -> SpeechBackend:
        preference = "qt" if self._selected_voice_id == QT_VOICE_ID else "auto"
        backend = create_speech_backend(
            preference=preference,  # type: ignore[arg-type]
            voices_dir=self._voices_dir,
            voice_id=self._selected_voice_id,
        )
        backend.set_finished_callback(self._on_speech_finished)
        return backend

    def _apply_speech_rate(self) -> None:
        self._speech.set_rate_from_wpm(
            self._engine.wpm,
            self._engine.speech_pace_multiplier(),
        )

    def _on_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        profile_id = self._profile_combo.itemData(index)
        if not profile_id or profile_id == self._engine.profile_id:
            return
        self._engine.set_profile(str(profile_id))
        self._settings.save_reading_profile(self._engine.profile_id)
        self._apply_speech_rate()
        self._update_status()
        if self._playing and self._tts_enabled:
            self._phrase_timer.setInterval(
                self._engine.interval_ms_at(self._display_position())
            )
        elif self._playing and not self._tts_enabled:
            self._timer.setInterval(self._engine.interval_ms())

    def _refresh_voice_combo(self) -> None:
        installed = list_installed_piper_voices(self._voices_dir)
        self._selected_voice_id = resolve_voice_selection(
            self._voices_dir,
            self._selected_voice_id,
            installed=installed,
        )

        self._voice_combo.blockSignals(True)
        self._voice_combo.clear()
        for voice_id in installed:
            self._voice_combo.addItem(voice_label(voice_id), voice_id)
        self._voice_combo.addItem(voice_label(QT_VOICE_ID), QT_VOICE_ID)

        index = self._voice_combo.findData(self._selected_voice_id)
        if index < 0:
            index = self._voice_combo.findData(QT_VOICE_ID)
        self._voice_combo.setCurrentIndex(max(index, 0))
        self._voice_combo.blockSignals(False)

        self._selected_voice_id = str(self._voice_combo.currentData())
        self._tts_button.setToolTip(f"Voz: {self._speech.name}")

    def _reload_speech_backend(self) -> None:
        was_playing = self._playing
        self._speech.stop()
        self._speech = self._create_speech_backend()
        self._apply_speech_rate()
        self._tts_button.setToolTip(f"Voz: {self._speech.name}")
        self._show_reading_position()
        self._update_status()
        if was_playing and self._tts_enabled and not self._engine.is_finished:
            self._speak_current()

    def _on_voice_changed(self, index: int) -> None:
        if index < 0:
            return
        voice_id = self._voice_combo.itemData(index)
        if not voice_id or voice_id == self._selected_voice_id:
            return

        self._selected_voice_id = str(voice_id)
        self._settings.save_tts_voice(self._selected_voice_id)
        self._reload_speech_backend()

    def _on_tts_toggled(self, enabled: bool) -> None:
        self._tts_enabled = enabled
        self._settings.save_tts_enabled(enabled)
        if not enabled:
            self._speech.stop()
            if self._playing and not self._engine.is_finished:
                self._timer.start(self._engine.interval_ms())
            self._show_reading_position()
            return
        self._apply_speech_rate()
        self._show_reading_position()
        if self._playing:
            self._timer.stop()
            self._speak_current()

    def _uses_phrase_tts(self) -> bool:
        return self._tts_enabled and self._speech.name.startswith("Piper")

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence.StandardKey.Open, self, self._open_file)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_playback)
        QShortcut(QKeySequence.StandardKey.Paste, self, self._paste_from_clipboard)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._previous_word)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._next_word)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._reset_reading)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self._toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._exit_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Question), self, self._show_shortcuts_help)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile() and is_supported_file(url.toLocalFile()):
                event.acceptProposedAction()
                return

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            file_path = url.toLocalFile()
            if is_supported_file(file_path):
                self._open_file_path(file_path)
                event.acceptProposedAction()
                return

    def _show_shortcuts_help(self) -> None:
        ShortcutsDialog(self).exec()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self) -> None:
        self._status_label.hide()
        self._progress_slider.hide()
        self._controls.hide()
        self._apply_word_font_size(self._focus_font_size(self._normal_word_point_size))
        self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        if not self.isFullScreen():
            return
        self.showNormal()
        self._status_label.show()
        self._progress_slider.show()
        self._controls.show()
        self._apply_word_font_size(self._normal_word_point_size)

    def _paste_from_clipboard(self) -> None:
        clipboard = ClipboardImporter()
        text = clipboard.read_text()
        if not text.strip():
            self._stop_playback()
            self._engine.load([])
            self._show_idle_message()
            self._update_status()
            self._play_button.setEnabled(False)
            self._reset_button.setEnabled(False)
            return

        self._load_segments(
            MarkdownImporter().parse(text),
            source="Clipboard",
            source_kind="clipboard",
        )

    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            "",
            "Text files (*.txt *.md *.markdown);;All files (*)",
        )
        if not file_path:
            return

        self._open_file_path(file_path)

    def _open_file_path(self, file_path: str) -> None:
        try:
            segments = FileImporter().read(file_path)
        except OSError:
            self._set_plain_message("Could not read file")
            return
        self._load_segments(segments, source=file_path, source_kind="file")

    def _load_segments(
        self,
        segments,
        source: str | None = None,
        source_kind: str | None = None,
        resume_position: int | None = None,
    ) -> None:
        self._stop_playback()
        self._source_path = source if source_kind == "file" else None
        self._source_kind = source_kind
        self._engine.load(segments)
        if self._engine.is_empty:
            self._set_plain_message("No readable text found")
            self._play_button.setEnabled(False)
            self._reset_button.setEnabled(False)
        else:
            if resume_position is not None:
                self._engine.seek(resume_position)
            else:
                self._engine.reset()
            self._show_reading_position()
            self._play_button.setEnabled(True)
            self._reset_button.setEnabled(True)
        self._sync_progress_slider()
        self._update_status()
        self._update_window_title(source)

    def _restore_reading_session(self) -> None:
        session = self._settings.load_reading_session()
        if session is None:
            return

        try:
            segments = FileImporter().read(session.source_path)
        except OSError:
            self._settings.clear_reading_session()
            return

        self._load_segments(
            segments,
            source=session.source_path,
            source_kind="file",
            resume_position=session.position,
        )

    def _persist_reading_session(self) -> None:
        if self._source_kind != "file" or not self._source_path or self._engine.is_empty:
            self._settings.clear_reading_session()
            return

        if self._engine.is_finished:
            position = 0
        else:
            position = self._engine.position

        self._settings.save_reading_session(self._source_path, position)

    def _update_window_title(self, source: str | None = None) -> None:
        if source:
            self.setWindowTitle(f"Speedreader — {source}")
        else:
            self.setWindowTitle("Speedreader")

    def _toggle_playback(self) -> None:
        if self._playing:
            self._stop_playback()
            return
        if self._engine.is_finished:
            self._engine.reset()
        self._playing = True
        self._play_button.setText("Pause")
        if self._tts_enabled:
            self._speak_current()
        else:
            self._timer.start(self._engine.interval_ms())
            self._show_reading_position()

    def _stop_playback(self) -> None:
        self._playing = False
        self._timer.stop()
        self._stop_phrase_visual_timer()
        self._speech.stop()
        self._play_button.setText("Play")

    def _stop_phrase_visual_timer(self) -> None:
        self._phrase_timer.stop()
        self._phrase_word_offset = 0

    def _display_position(self) -> int:
        if self._phrase_timer.isActive():
            return self._engine.position + self._phrase_word_offset
        return self._engine.position

    def _should_skip_tts_for_current_unit(self) -> bool:
        return self._engine.current_segment_kind == SegmentKind.CODE_BLOCK

    def _speak_current(self) -> None:
        if self._uses_phrase_tts():
            self._speak_current_phrase()
        else:
            self._speak_current_word()

    def _speak_current_word(self) -> None:
        if not self._playing:
            return
        if self._engine.is_finished:
            self._stop_playback()
            self._set_plain_message("Done")
            return
        self._show_current_word()
        if self._should_skip_tts_for_current_unit():
            self._on_speech_finished()
            return
        word = self._engine.current_word
        if not word:
            self._on_speech_finished()
            return
        self._apply_speech_rate()
        self._speech.speak(word)

    def _speak_current_phrase(self) -> None:
        if not self._playing:
            return
        if self._engine.is_finished:
            self._stop_playback()
            self._set_plain_message("Done")
            return
        if self._should_skip_tts_for_current_unit():
            self._on_speech_finished()
            return
        phrase = self._engine.current_phrase_text()
        if not phrase:
            self._on_speech_finished()
            return
        self._phrase_word_offset = 0
        self._show_phrase_word_at_offset(0)
        self._apply_speech_rate()
        self._speech.speak(phrase)
        self._phrase_timer.start(self._engine.interval_ms_at(self._engine.position))

    def _on_phrase_visual_tick(self) -> None:
        phrase_end = self._engine.phrase_end_position()
        next_index = self._engine.position + self._phrase_word_offset + 1
        if next_index >= phrase_end:
            self._phrase_timer.stop()
            return
        self._phrase_word_offset += 1
        self._show_phrase_word_at_offset(self._phrase_word_offset)
        self._update_status()
        self._phrase_timer.setInterval(self._engine.interval_ms_at(next_index))

    def _on_speech_finished(self) -> None:
        if not self._playing or not self._tts_enabled:
            return
        self._stop_phrase_visual_timer()
        if self._uses_phrase_tts():
            self._engine.advance_phrase()
        else:
            self._engine.advance()
        self._update_status()
        if self._engine.is_finished:
            self._stop_playback()
            self._set_plain_message("Done")
            return
        self._speak_current()

    def _reset_reading(self) -> None:
        self._stop_playback()
        self._engine.reset()
        self._show_reading_position()
        self._update_status()

    def _previous_word(self) -> None:
        if self._engine.is_empty:
            return
        self._stop_playback()
        if self._uses_phrase_tts():
            self._engine.retreat_phrase()
        else:
            self._engine.retreat()
        self._show_reading_position()
        self._update_status()

    def _next_word(self) -> None:
        if self._engine.is_empty or self._engine.is_finished:
            return
        self._stop_playback()
        if self._uses_phrase_tts():
            self._engine.advance_to_next_phrase()
        else:
            self._engine.advance()
        if self._engine.is_finished:
            self._set_plain_message("Done")
        else:
            self._show_reading_position()
        self._update_status()

    def _on_tick(self) -> None:
        if self._tts_enabled:
            return
        self._engine.advance()
        self._update_status()
        if self._engine.is_finished:
            self._stop_playback()
            self._set_plain_message("Done")
            return
        self._show_reading_position()
        self._timer.setInterval(self._engine.interval_ms())

    def _on_wpm_changed(self, value: int) -> None:
        self._engine.wpm = value
        self._wpm_label.setText(f"{value} WPM")
        self._settings.save_wpm(value)
        self._apply_speech_rate()
        self._update_status()
        if self._playing and not self._tts_enabled:
            self._timer.setInterval(self._engine.interval_ms())

    def _on_font_size_changed(self, value: int) -> None:
        self._normal_word_point_size = value
        self._font_label.setText(f"{value} pt")
        self._settings.save_font_size(value)
        if self.isFullScreen():
            self._apply_word_font_size(self._focus_font_size(value))
        else:
            self._apply_word_font_size(value)

    def _focus_font_size(self, normal_size: int) -> int:
        return min(normal_size + 14, MAX_FONT_SIZE + 14)

    def _apply_word_font_size(self, point_size: int) -> None:
        word_font = self._word_label.font()
        word_font.setPointSize(point_size)
        word_font.setBold(True)
        self._word_label.setFont(word_font)

    def _set_plain_message(self, message: str) -> None:
        self._word_label.setTextFormat(Qt.TextFormat.PlainText)
        self._word_label.setText(message)

    def _show_reading_position(self) -> None:
        if self._uses_phrase_tts() and self._phrase_timer.isActive():
            self._show_phrase_word_at_offset(self._phrase_word_offset)
        elif self._uses_phrase_tts():
            self._show_current_phrase()
        else:
            self._show_current_word()

    def _show_phrase_word_at_offset(self, offset: int) -> None:
        token = self._engine.token_at(self._engine.position + offset)
        if token is None:
            self._set_plain_message("Done")
            return
        self._word_label.setWordWrap(False)
        self._word_label.setTextFormat(Qt.TextFormat.RichText)
        self._word_label.setText(format_word_with_orp(token.text))

    def _show_current_phrase(self) -> None:
        phrase = self._engine.current_phrase_text()
        if phrase is None:
            self._set_plain_message("Done")
            return
        self._word_label.setWordWrap(True)
        self._set_plain_message(phrase)

    def _show_current_word(self) -> None:
        self._word_label.setWordWrap(False)
        word = self._engine.current_word
        if word is None:
            self._set_plain_message("Done")
            return
        self._word_label.setTextFormat(Qt.TextFormat.RichText)
        self._word_label.setText(format_word_with_orp(word))

    def _on_progress_changed(self, value: int) -> None:
        if not self._progress_slider.isSliderDown():
            return
        self._stop_playback()
        self._engine.seek(value)
        self._show_reading_position()
        self._update_status()

    def _sync_progress_slider(self) -> None:
        total = self._engine.word_count
        self._progress_slider.blockSignals(True)
        self._progress_slider.setEnabled(total > 0)
        maximum = max(total - 1, 0)
        self._progress_slider.setMaximum(maximum)
        if total == 0:
            self._progress_slider.setValue(0)
        elif self._engine.is_finished:
            self._progress_slider.setValue(maximum)
        else:
            self._progress_slider.setValue(self._display_position())
        self._progress_slider.blockSignals(False)

    def _update_status(self) -> None:
        if self._engine.is_empty:
            self._status_label.setText(f"{IDLE_HINT} · {self._mode_summary()}")
            self._sync_progress_slider()
            return

        total = self._engine.word_count
        current = min(self._display_position() + (0 if self._engine.is_finished else 1), total)
        if total == 0:
            current = 0
        self._status_label.setText(
            f"{current} / {total} words · {self._engine.wpm} WPM · {self._mode_summary()}"
        )
        if not self._progress_slider.isSliderDown():
            self._sync_progress_slider()

    def _mode_summary(self) -> str:
        parts = [self._settings.load_reading_profile_label()]
        if self._tts_enabled:
            parts.append(self._speech.name)
            if self._uses_phrase_tts():
                parts.append("frases + RSVP")
            else:
                parts.append("palabras")
        else:
            parts.append("RSVP")
        return " · ".join(parts)
