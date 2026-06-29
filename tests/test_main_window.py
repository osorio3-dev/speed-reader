"""UI tests for the main window."""

from __future__ import annotations

import pytest

from speedreader.domain import SegmentKind, TextSegment
from speedreader.ui.main_window import IDLE_HINT, IDLE_MESSAGE, MainWindow


class _FakeSpeech:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rate_calls: list[tuple[int, float]] = []

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        self.rate_calls.append((wpm, pace_multiplier))

    def set_finished_callback(self, callback) -> None:
        self._callback = callback

    def speak(self, text: str) -> None:
        self.last_text = text

    def stop(self) -> None:
        pass


@pytest.fixture
def main_window(qapp):
    window = MainWindow()
    yield window
    window.close()


def test_idle_screen_shows_brand_and_hint(main_window: MainWindow) -> None:
    assert main_window._word_label.text() == IDLE_MESSAGE
    assert IDLE_HINT in main_window._status_label.text()
    assert main_window._settings.load_reading_profile_label() in main_window._status_label.text()
    assert "RSVP" in main_window._status_label.text() or "frases + RSVP" in main_window._status_label.text()


def test_phrase_tts_mode_requires_piper(main_window: MainWindow) -> None:
    main_window._tts_enabled = True
    main_window._speech = _FakeSpeech("Piper (es_MX-ald-x_low)")
    assert main_window._uses_phrase_tts()

    main_window._speech = _FakeSpeech("Qt")
    assert not main_window._uses_phrase_tts()


def test_profile_change_updates_engine_and_speech_rate(main_window: MainWindow) -> None:
    main_window._speech = _FakeSpeech("Qt")
    main_window._engine.load([TextSegment("Title here.", SegmentKind.HEADING)])
    normal_index = main_window._profile_combo.findData("normal")
    main_window._profile_combo.setCurrentIndex(normal_index)
    main_window._speech.rate_calls.clear()
    study_index = main_window._profile_combo.findData("study")
    assert study_index >= 0
    main_window._profile_combo.setCurrentIndex(study_index)
    assert main_window._engine.profile_id == "study"
    assert main_window._speech.rate_calls


def test_arrow_navigation_uses_phrases_with_piper(main_window: MainWindow) -> None:
    main_window._speech = _FakeSpeech("Piper (test)")
    main_window._tts_enabled = True
    main_window._engine.load(
        [TextSegment("Uno dos. Tres cuatro.", SegmentKind.PARAGRAPH)]
    )
    main_window._engine.advance()
    main_window._next_word()
    assert main_window._engine.current_word == "Tres"

    main_window._previous_word()
    assert main_window._engine.current_word == "Uno"


def test_mode_summary_reflects_tts_and_profile(main_window: MainWindow) -> None:
    main_window._speech = _FakeSpeech("Piper (es_MX-ald-x_low)")
    main_window._tts_enabled = True
    summary = main_window._mode_summary()
    assert main_window._settings.load_reading_profile_label() in summary
    assert "Piper" in summary
    assert "frases + RSVP" in summary
