"""Main application window for RSVP speed reading."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
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

from speedreader.engine import DEFAULT_WPM, ReadingEngine
from speedreader.importers.clipboard import ClipboardImporter
from speedreader.orp import format_word_with_orp
from speedreader.importers.file import FileImporter
from speedreader.importers.markdown import MarkdownImporter


class MainWindow(QMainWindow):
    """RSVP reader with paste, play/pause, and WPM controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Speedreader")
        self.resize(720, 360)

        self._engine = ReadingEngine()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._playing = False

        self._word_label = QLabel("Paste or open a file to begin")
        self._word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        word_font = QFont()
        word_font.setPointSize(42)
        word_font.setBold(True)
        self._word_label.setFont(word_font)

        self._status_label = QLabel(f"0 / 0 words · {DEFAULT_WPM} WPM")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self._wpm_slider.setRange(100, 1000)
        self._wpm_slider.setValue(self._engine.wpm)
        self._wpm_slider.setTickInterval(100)
        self._wpm_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._wpm_slider.valueChanged.connect(self._on_wpm_changed)

        self._wpm_label = QLabel(f"{self._engine.wpm} WPM")

        controls = QHBoxLayout()
        controls.addWidget(self._open_button)
        controls.addWidget(self._paste_button)
        controls.addWidget(self._play_button)
        controls.addWidget(self._reset_button)
        controls.addStretch()
        controls.addWidget(self._wpm_label)
        controls.addWidget(self._wpm_slider)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self._word_label)
        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addLayout(controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence.StandardKey.Open, self, self._open_file)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_playback)
        QShortcut(QKeySequence.StandardKey.Paste, self, self._paste_from_clipboard)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self._previous_word)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self._next_word)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._reset_reading)

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

        self._load_segments(MarkdownImporter().parse(text), source="Clipboard")

    def _open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            "",
            "Text files (*.txt *.md *.markdown);;All files (*)",
        )
        if not file_path:
            return

        segments = FileImporter().read(file_path)
        self._load_segments(segments, source=file_path)

    def _load_segments(self, segments, source: str | None = None) -> None:
        self._stop_playback()
        self._engine.load(segments)
        if self._engine.is_empty:
            self._set_plain_message("No readable text found")
            self._play_button.setEnabled(False)
            self._reset_button.setEnabled(False)
        else:
            self._engine.reset()
            self._show_current_word()
            self._play_button.setEnabled(True)
            self._reset_button.setEnabled(True)
        self._update_status()
        self._update_window_title(source)

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
        self._update_status()
        if self._playing:
            self._timer.setInterval(self._engine.interval_ms())

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

    def _update_status(self) -> None:
        total = self._engine.word_count
        current = min(self._engine.position + (0 if self._engine.is_finished else 1), total)
        if total == 0:
            current = 0
        self._status_label.setText(
            f"{current} / {total} words · {self._engine.wpm} WPM"
        )
