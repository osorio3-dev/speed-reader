"""Main application window for RSVP speed reading.

Thin view: owns widgets, layout, drag-drop, and keyboard shortcuts.
Playback state and timers live in ReadingController.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
from speedreader.importers.clipboard import ClipboardImporter
from speedreader.importers.file import FileImporter, is_supported_file
from speedreader.importers.markdown import MarkdownImporter
from speedreader.orp import format_word_with_orp
from speedreader.settings import (
    MAX_FONT_SIZE,
    MAX_WPM,
    MIN_FONT_SIZE,
    MIN_WPM,
    SettingsStore,
    WPM_STEP,
    snap_wpm,
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
from speedreader.ui.reading_controller import ReadingController
from speedreader.ui.shortcuts_dialog import ShortcutsDialog

IDLE_MESSAGE = "-- Speedreader --"
IDLE_HINT = "Pega, abre (Ctrl+O) o arrastra un .txt / .md"


class MainWindow(QMainWindow):
    """RSVP reader with paste, play/pause, and WPM controls.

    Signals
    -------
    play_requested : emitted when the user wants to start/resume (wired to controller).
    pause_requested : emitted when the user wants to pause (wired to controller).
    seek_requested(int) : emitted when the user drags the progress slider.
    """

    play_requested = Signal()
    pause_requested = Signal()
    seek_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Speedreader")
        self.resize(720, 360)
        self.setAcceptDrops(True)

        # -- Persistent settings --
        self._settings = SettingsStore()

        # -- Backing stores for property shims (set before controller exists) --
        _engine = ReadingEngine(
            wpm=self._settings.load_wpm(),
            profile_id=self._settings.load_reading_profile(),
        )
        self._engine_backing = _engine
        self._speech_backing = None  # set below

        self._normal_word_point_size = self._settings.load_font_size()
        self._voices_dir = self._settings.load_voices_dir()
        self._selected_voice_id = resolve_voice_selection(
            self._voices_dir,
            self._settings.load_tts_voice(),
        )
        _speech = self._create_speech_backend()
        self._speech_backing = _speech

        # -- Controller (owns timers, playback state, emits signals) --
        self._controller = ReadingController(
            _engine, _speech, self._settings, self,
        )
        self._controller.word_changed.connect(self._on_word_changed)
        self._controller.status_changed.connect(self._on_status_changed)
        self._controller.finished.connect(self._on_reading_finished)
        self._controller.progress_changed.connect(self._on_progress_changed)

        # Wire view signals to controller API
        self.play_requested.connect(self._controller.play)
        self.pause_requested.connect(self._controller.pause)
        self.seek_requested.connect(self._controller.seek)

        # -- Widgets --
        self._word_label = QLabel(IDLE_MESSAGE)
        self._word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_word_font_size(self._normal_word_point_size)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setEnabled(False)
        self._progress_slider.valueChanged.connect(self._on_progress_dragged)

        self._paste_button = QPushButton("Paste")
        self._paste_button.clicked.connect(self._paste_from_clipboard)

        self._open_button = QPushButton("Open")
        self._open_button.clicked.connect(self._open_file)

        self._play_button = QPushButton("Play")
        self._play_button.clicked.connect(self._on_play_clicked)
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
        self._wpm_slider.setSingleStep(WPM_STEP)
        self._wpm_slider.setPageStep(100)
        self._wpm_slider.setValue(snap_wpm(self._engine.wpm))
        self._wpm_slider.setTickInterval(WPM_STEP)
        self._wpm_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._wpm_slider.valueChanged.connect(self._on_wpm_changed)

        self._wpm_label = QLabel(self._format_rsvp_wpm_label())

        self._tts_wpm_slider = QSlider(Qt.Orientation.Horizontal)
        self._tts_wpm_slider.setRange(MIN_WPM, MAX_WPM)
        self._tts_wpm_slider.setSingleStep(WPM_STEP)
        self._tts_wpm_slider.setPageStep(100)
        self._tts_wpm_slider.setValue(snap_wpm(self._tts_wpm))
        self._tts_wpm_slider.setTickInterval(WPM_STEP)
        self._tts_wpm_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._tts_wpm_slider.valueChanged.connect(self._on_tts_wpm_changed)

        self._tts_wpm_label = QLabel(self._format_tts_wpm_label())

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

        # -- Layout --
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
        tts_wpm_row = QHBoxLayout()
        tts_wpm_row.addWidget(self._tts_wpm_label)
        tts_wpm_row.addWidget(self._tts_wpm_slider)
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Perfil"))
        profile_row.addWidget(self._profile_combo)
        tuning.addLayout(font_row)
        tuning.addLayout(wpm_row)
        tuning.addLayout(tts_wpm_row)
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

        self._sync_tts_controls()

    # ------------------------------------------------------------------
    # Backward-compatible property shims (used by existing tests)
    # Backing stores allow access before ReadingController is created.
    # ------------------------------------------------------------------

    @property
    def _engine(self) -> ReadingEngine:
        if hasattr(self, '_controller'):
            return self._controller.engine
        return self._engine_backing

    @_engine.setter
    def _engine(self, value: ReadingEngine) -> None:
        self._engine_backing = value
        if hasattr(self, '_controller'):
            self._controller._engine = value  # type: ignore[assignment]

    @property
    def _speech(self) -> SpeechBackend:
        if hasattr(self, '_controller'):
            return self._controller.speech
        return self._speech_backing

    @_speech.setter
    def _speech(self, backend: SpeechBackend) -> None:
        self._speech_backing = backend
        if hasattr(self, '_controller'):
            self._controller.speech = backend

    @property
    def _playing(self) -> bool:
        return self._controller.playing

    @_playing.setter
    def _playing(self, value: bool) -> None:
        self._controller._playing = value  # type: ignore[assignment]

    @property
    def _tts_enabled(self) -> bool:
        return self._controller.tts_enabled

    @_tts_enabled.setter
    def _tts_enabled(self, value: bool) -> None:
        self._controller.tts_enabled = value

    @property
    def _tts_wpm(self) -> int:
        return self._controller.tts_wpm

    @_tts_wpm.setter
    def _tts_wpm(self, value: int) -> None:
        self._controller.tts_wpm = value

    @property
    def _source_path(self) -> str | None:
        if not hasattr(self, '_controller'):
            return None
        return self._controller.source_path

    @_source_path.setter
    def _source_path(self, value: str | None) -> None:
        if hasattr(self, '_controller'):
            self._controller._source_path = value  # type: ignore[assignment]

    @property
    def _source_kind(self) -> str | None:
        if not hasattr(self, '_controller'):
            return None
        return self._controller.source_kind

    @_source_kind.setter
    def _source_kind(self, value: str | None) -> None:
        if hasattr(self, '_controller'):
            self._controller._source_kind = value  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # Backward-compatible method shims (used by existing tests)
    # ------------------------------------------------------------------

    def _stop_playback(self) -> None:
        self._controller.stop()

    def _toggle_playback(self) -> None:
        self._controller.toggle()

    def _reset_reading(self) -> None:
        self._controller.stop()
        self._controller.engine.reset()
        self._show_reading_position()
        self._update_status()

    def _previous_word(self) -> None:
        self._controller.previous_word()

    def _next_word(self) -> None:
        self._controller.next_word()

    def _display_position(self) -> int:
        return self._controller.display_position()

    def _uses_phrase_tts(self) -> bool:
        return self._controller._uses_phrase_tts()  # type: ignore[return-value]

    def _apply_speech_rate(self) -> None:
        self._controller._apply_speech_rate()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # View helpers
    # ------------------------------------------------------------------

    def _format_rsvp_wpm_label(self) -> str:
        return f"RSVP {self._engine.wpm}"

    def _format_tts_wpm_label(self) -> str:
        return f"TTS {self._tts_wpm}"

    def _sync_tts_controls(self) -> None:
        enabled = self._tts_enabled
        self._tts_wpm_slider.setEnabled(enabled)
        self._tts_wpm_label.setEnabled(enabled)

    def _show_idle_message(self) -> None:
        self._set_plain_message(IDLE_MESSAGE)
        self._update_status()

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

    # ------------------------------------------------------------------
    # Controller signal handlers
    # ------------------------------------------------------------------

    def _on_word_changed(self, text: str) -> None:
        """Update the word label when the controller emits a new word."""
        # Phrases (plain text with spaces) use word-wrap + PlainText;
        # individual ORP-highlighted words use RichText + no wrap.
        if self._uses_phrase_tts() and " " in text and "<span" not in text:
            self._word_label.setWordWrap(True)
            self._word_label.setTextFormat(Qt.TextFormat.PlainText)
            self._word_label.setText(text)
        else:
            self._word_label.setWordWrap(False)
            self._word_label.setTextFormat(Qt.TextFormat.RichText)
            self._word_label.setText(text)

    def _on_status_changed(self, status: str) -> None:
        """React to status changes (update play button, status bar)."""
        if status == "playing":
            self._play_button.setText("Pause")
        else:
            self._play_button.setText("Play")
        self._update_status()

    def _on_reading_finished(self) -> None:
        """Reading reached the end."""
        self._update_status()

    def _on_progress_changed(self, position: int, total: int) -> None:
        """Sync the progress slider (unless the user is dragging it)."""
        if not self._progress_slider.isSliderDown():
            self._sync_progress_slider()
            self._update_status()

    # ------------------------------------------------------------------
    # Widget event handlers
    # ------------------------------------------------------------------

    def _on_play_clicked(self) -> None:
        """Play/pause button clicked — emit the appropriate signal."""
        if self._controller.playing:
            self.pause_requested.emit()
        else:
            self.play_requested.emit()

    def _on_progress_dragged(self, value: int) -> None:
        """User dragged the progress slider."""
        if not self._progress_slider.isSliderDown():
            return
        self.seek_requested.emit(value)

    def _on_wpm_changed(self, value: int) -> None:
        snapped = snap_wpm(value)
        if snapped != value:
            self._wpm_slider.blockSignals(True)
            self._wpm_slider.setValue(snapped)
            self._wpm_slider.blockSignals(False)
            value = snapped
        self._controller.set_wpm(value)
        self._wpm_label.setText(self._format_rsvp_wpm_label())
        self._settings.save_wpm(value)
        self._update_status()

    def _on_tts_wpm_changed(self, value: int) -> None:
        snapped = snap_wpm(value)
        if snapped != value:
            self._tts_wpm_slider.blockSignals(True)
            self._tts_wpm_slider.setValue(snapped)
            self._tts_wpm_slider.blockSignals(False)
            value = snapped
        self._controller.set_tts_wpm(value)
        self._tts_wpm_label.setText(self._format_tts_wpm_label())
        self._settings.save_tts_wpm(value)
        self._update_status()

    def _on_font_size_changed(self, value: int) -> None:
        self._normal_word_point_size = value
        self._font_label.setText(f"{value} pt")
        self._settings.save_font_size(value)
        if self.isFullScreen():
            self._apply_word_font_size(self._focus_font_size(value))
        else:
            self._apply_word_font_size(value)

    def _on_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        profile_id = self._profile_combo.itemData(index)
        if not profile_id or profile_id == self._engine.profile_id:
            return
        self._controller.set_profile(str(profile_id))
        self._settings.save_reading_profile(self._engine.profile_id)
        self._update_status()

    def _on_tts_toggled(self, enabled: bool) -> None:
        self._controller.tts_enabled = enabled
        self._settings.save_tts_enabled(enabled)
        self._sync_tts_controls()
        self._show_reading_position()
        self._update_status()

    def _on_voice_changed(self, index: int) -> None:
        if index < 0:
            return
        voice_id = self._voice_combo.itemData(index)
        if not voice_id or voice_id == self._selected_voice_id:
            return
        self._selected_voice_id = str(voice_id)
        self._settings.save_tts_voice(self._selected_voice_id)
        self._reload_speech_backend()

    # ------------------------------------------------------------------
    # Speech / Voice
    # ------------------------------------------------------------------

    def _create_speech_backend(self) -> SpeechBackend:
        preference = "qt" if self._selected_voice_id == QT_VOICE_ID else "auto"
        backend = create_speech_backend(
            preference=preference,  # type: ignore[arg-type]
            voices_dir=self._voices_dir,
            voice_id=self._selected_voice_id,
        )
        # Note: finished callback is set by ReadingController after construction
        return backend

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
        new_backend = self._create_speech_backend()
        self._controller.set_speech_backend(new_backend)
        self._tts_button.setToolTip(f"Voz: {self._speech.name}")
        self._show_reading_position()
        self._update_status()

    # ------------------------------------------------------------------
    # Reading session (file persistence)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # File / Clipboard loading
    # ------------------------------------------------------------------

    def _paste_from_clipboard(self) -> None:
        clipboard = ClipboardImporter()
        text = clipboard.read_text()
        if not text.strip():
            self._controller.stop()
            self._controller.load([])
            self._show_idle_message()
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
        self._controller.load(segments, source, source_kind, resume_position)
        if self._engine.is_empty:
            self._set_plain_message("No readable text found")
            self._play_button.setEnabled(False)
            self._reset_button.setEnabled(False)
        else:
            if resume_position is None:
                self._show_reading_position()
            self._play_button.setEnabled(True)
            self._reset_button.setEnabled(True)
        self._sync_progress_slider()
        self._update_status()
        self._update_window_title(source)

    # ------------------------------------------------------------------
    # Display updates
    # ------------------------------------------------------------------

    def _show_reading_position(self) -> None:
        """Update the word label to reflect the current engine position."""
        if self._uses_phrase_tts():
            if self._controller._phrase_timer.isActive():  # type: ignore[attr]
                token = self._engine.token_at(
                    self._engine.position + self._controller._phrase_word_offset  # type: ignore[attr]
                )
                if token is not None:
                    self._word_label.setWordWrap(False)
                    self._word_label.setTextFormat(Qt.TextFormat.RichText)
                    self._word_label.setText(format_word_with_orp(token.text))
                    return
            phrase = self._engine.current_phrase_text()
            if phrase is not None:
                self._word_label.setWordWrap(True)
                self._set_plain_message(phrase)
                return
        word = self._engine.current_word
        if word is not None:
            self._word_label.setWordWrap(False)
            self._word_label.setTextFormat(Qt.TextFormat.RichText)
            self._word_label.setText(format_word_with_orp(word))
        else:
            self._set_plain_message("Done")

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
            f"{current} / {total} words · RSVP {self._engine.wpm}"
            + (f" · TTS {self._tts_wpm}" if self._tts_enabled else "")
            + f" · {self._mode_summary()}"
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

    # ------------------------------------------------------------------
    # Fullscreen
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Close / Persist
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        self._settings.save_wpm(self._engine.wpm)
        self._settings.save_tts_wpm(self._tts_wpm)
        self._settings.save_font_size(self._normal_word_point_size)
        self._settings.save_tts_enabled(self._tts_enabled)
        self._settings.save_tts_voice(self._selected_voice_id)
        self._settings.save_reading_profile(self._engine.profile_id)
        self._persist_reading_session()
        self._speech.stop()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Drag / Drop
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence.StandardKey.Open, self, self._open_file)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_play_clicked)
        QShortcut(QKeySequence.StandardKey.Paste, self, self._paste_from_clipboard)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._previous_word)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._next_word)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._reset_reading)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self._toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._exit_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Question), self, self._show_shortcuts_help)

    def _show_shortcuts_help(self) -> None:
        ShortcutsDialog(self).exec()

    def _update_window_title(self, source: str | None = None) -> None:
        if source:
            self.setWindowTitle(f"Speedreader — {source}")
        else:
            self.setWindowTitle("Speedreader")
