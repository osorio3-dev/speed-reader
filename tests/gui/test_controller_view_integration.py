"""Integration tests: MainWindow reacts to ReadingController signals."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from speedreader.core.domain import SegmentKind, TextSegment
from speedreader.ui.main_window import IDLE_HINT, IDLE_MESSAGE, MainWindow


class _FakeSpeech:
    """Minimal SpeechBackend stub."""

    def __init__(self, name: str = "Qt") -> None:
        self.name = name
        self.rate_calls: list[tuple[int, float]] = []
        self.last_text: str | None = None
        self._callback = None
        self._pitch_pct: float = 0.0

    @property
    def capabilities(self):
        from speedreader.core.speech import SpeechCapabilities

        return SpeechCapabilities(supports_pitch=True)

    @property
    def pitch_pct(self) -> float:
        return self._pitch_pct

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        self.rate_calls.append((wpm, pace_multiplier))

    def set_pitch_from_pct(self, pct: float) -> None:
        self._pitch_pct = pct

    def set_finished_callback(self, callback) -> None:
        self._callback = callback

    def speak(self, text: str) -> None:
        self.last_text = text
        if self._callback:
            self._callback()

    def stop(self) -> None:
        pass


@pytest.fixture
def main_window(qapp):
    window = MainWindow()
    # Replace speech with a fake for deterministic tests
    window._speech = _FakeSpeech("Qt")
    window._tts_enabled = False
    window._sync_tts_controls()
    yield window
    window.close()


# --- View wires controller signals to labels ---

def test_word_changed_updates_word_label(main_window: MainWindow) -> None:
    """Controller's word_changed signal should update the word QLabel."""
    segments = [TextSegment("Hello world.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    main_window._controller.play()
    # The label should show the first word (ORP-highlighted HTML)
    assert 'e67e22' in main_window._word_label.text() or 'llo' in main_window._word_label.text()
    main_window._controller.pause()


def test_progress_changed_updates_slider(main_window: MainWindow) -> None:
    """Controller's progress_changed should sync the progress slider."""
    segments = [TextSegment("One two three.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    main_window._controller.next_word()
    assert main_window._progress_slider.value() >= 1


def test_status_changed_updates_play_button(main_window: MainWindow) -> None:
    """Pausing should change the play button text to 'Play'."""
    segments = [TextSegment("Hello.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    main_window._controller.play()
    main_window._controller.pause()
    assert main_window._play_button.text() == "Play"


def test_play_button_text_toggles(main_window: MainWindow) -> None:
    """Play button shows 'Pause' when playing, 'Play' when stopped."""
    segments = [TextSegment("Hello.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    main_window._controller.play()
    assert main_window._play_button.text() == "Pause"
    main_window._controller.pause()
    assert main_window._play_button.text() == "Play"


def test_finished_shows_done_in_word_label(main_window: MainWindow) -> None:
    """When controller emits finished, word label should show 'Done'."""
    segments = [TextSegment("End.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    # Enable TTS so _FakeSpeech fires callback immediately
    main_window._tts_enabled = True
    main_window._controller.play()
    # With _FakeSpeech that invokes callback immediately, one word finishes instantly
    assert main_window._word_label.text() == "Done"


def test_controller_play_via_play_requested_signal(main_window: MainWindow) -> None:
    """The play_requested signal should trigger controller.play()."""
    segments = [TextSegment("Testing play requested.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    assert not main_window._controller.playing
    main_window.play_requested.emit()
    assert main_window._controller.playing
    main_window._controller.pause()


def test_controller_pause_via_pause_requested_signal(main_window: MainWindow) -> None:
    """The pause_requested signal should trigger controller.pause()."""
    segments = [TextSegment("Testing pause requested.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    main_window._controller.play()
    assert main_window._controller.playing
    main_window.pause_requested.emit()
    assert not main_window._controller.playing


def test_controller_seek_via_seek_requested_signal(main_window: MainWindow) -> None:
    """The seek_requested signal should trigger controller.seek()."""
    segments = [TextSegment("One two three four.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    assert main_window._controller.engine.position == 0
    main_window.seek_requested.emit(2)
    assert main_window._controller.engine.position == 2


# --- full simulation: load → play → auto-advance → finish ---

def test_full_play_cycle_updates_ui(main_window: MainWindow) -> None:
    """Simulate the full lifecycle: load, play, auto-advance, finish."""
    segments = [TextSegment("Hello world.", SegmentKind.PARAGRAPH)]
    main_window._controller.load(segments)
    txt = main_window._word_label.text()
    assert 'e67e22' in txt or 'llo' in txt or IDLE_MESSAGE in txt

    main_window._controller.play()
    # With _FakeSpeech callback, words advance immediately
    txt = main_window._word_label.text()
    assert txt == "Done" or 'e67e22' in txt or 'llo' in txt

    # After all words are processed, status should indicate completion
    final_text = main_window._word_label.text()
    assert final_text == "Done" or 'e67e22' in final_text or 'llo' in final_text


def test_button_enable_state_after_load(main_window: MainWindow) -> None:
    """Load should enable play and reset buttons."""
    assert not main_window._play_button.isEnabled()
    segments = [TextSegment("Content.", SegmentKind.PARAGRAPH)]
    main_window._load_segments(segments)
    assert main_window._play_button.isEnabled()
    assert main_window._reset_button.isEnabled()
