"""Main application window for RSVP speed reading."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
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
from speedreader.ui.shortcuts_dialog import ShortcutsDialog


class MainWindow(QMainWindow):
    """RSVP reader with paste, play/pause, and WPM controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Speedreader")
        self.resize(720, 360)
        self.setAcceptDrops(True)

        self._settings = SettingsStore()
        self._engine = ReadingEngine(wpm=self._settings.load_wpm())
        self._normal_word_point_size = self._settings.load_font_size()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._playing = False
        self._source_path: str | None = None
        self._source_kind: str | None = None

        self._word_label = QLabel("Paste, open, or drop a file to begin")
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

        self._wpm_slider = QSlider(Qt.Orientation.Horizontal)
        self._wpm_slider.setRange(MIN_WPM, MAX_WPM)
        self._wpm_slider.setValue(self._engine.wpm)
        self._wpm_slider.setTickInterval(100)
        self._wpm_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._wpm_slider.valueChanged.connect(self._on_wpm_changed)

        self._wpm_label = QLabel(f"{self._engine.wpm} WPM")

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
        controls.addStretch()

        tuning = QVBoxLayout()
        font_row = QHBoxLayout()
        font_row.addWidget(self._font_label)
        font_row.addWidget(self._font_slider)
        wpm_row = QHBoxLayout()
        wpm_row.addWidget(self._wpm_label)
        wpm_row.addWidget(self._wpm_slider)
        tuning.addLayout(font_row)
        tuning.addLayout(wpm_row)
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

    def closeEvent(self, event: QCloseEvent) -> None:
        self._settings.save_wpm(self._engine.wpm)
        self._settings.save_font_size(self._normal_word_point_size)
        self._persist_reading_session()
        super().closeEvent(event)

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
            self._set_plain_message("Clipboard is empty")
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
            self._show_current_word()
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
        self._timer.start(self._engine.interval_ms())
        self._show_current_word()

    def _stop_playback(self) -> None:
        self._playing = False
        self._timer.stop()
        self._play_button.setText("Play")

    def _reset_reading(self) -> None:
        self._stop_playback()
        self._engine.reset()
        self._show_current_word()
        self._update_status()

    def _previous_word(self) -> None:
        if self._engine.is_empty:
            return
        self._stop_playback()
        self._engine.retreat()
        self._show_current_word()
        self._update_status()

    def _next_word(self) -> None:
        if self._engine.is_empty or self._engine.is_finished:
            return
        self._stop_playback()
        self._engine.advance()
        if self._engine.is_finished:
            self._set_plain_message("Done")
        else:
            self._show_current_word()
        self._update_status()

    def _on_tick(self) -> None:
        self._engine.advance()
        self._update_status()
        if self._engine.is_finished:
            self._stop_playback()
            self._set_plain_message("Done")
            return
        self._show_current_word()
        self._timer.setInterval(self._engine.interval_ms())

    def _on_wpm_changed(self, value: int) -> None:
        self._engine.wpm = value
        self._wpm_label.setText(f"{value} WPM")
        self._settings.save_wpm(value)
        self._update_status()
        if self._playing:
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

    def _show_current_word(self) -> None:
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
        self._show_current_word()
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
            self._progress_slider.setValue(self._engine.position)
        self._progress_slider.blockSignals(False)

    def _update_status(self) -> None:
        total = self._engine.word_count
        current = min(self._engine.position + (0 if self._engine.is_finished else 1), total)
        if total == 0:
            current = 0
        self._status_label.setText(
            f"{current} / {total} words · {self._engine.wpm} WPM"
        )
        if not self._progress_slider.isSliderDown():
            self._sync_progress_slider()
