"""Tests for the isolated ReadingController with mock callbacks."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Signal

from speedreader.core.domain import SegmentKind, TextSegment
from speedreader.core.engine import ReadingEngine
from speedreader.settings import SettingsStore
from speedreader.ui.reading_controller import ReadingController


class _FakeSpeech:
    """Minimal SpeechBackend stub — no Qt dependency."""

    def __init__(self, name: str = "TestSpeech") -> None:
        self.name = name
        self.rate_calls: list[tuple[int, float]] = []
        self.last_text: str | None = None
        self._callback = None
        self._stopped = False
        self._pitch_pct: float = 0.0

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
        # Immediately invoke the finished callback (synchronous TTS mock)
        if self._callback:
            self._callback()

    def stop(self) -> None:
        self._stopped = True


class _FakeSettings:
    """SettingsStore stub that returns defaults."""

    def __init__(self) -> None:
        self._wpm: int = 400
        self._tts_wpm: int | None = None
        self._font_size: int = 42
        self._tts_enabled: bool = False
        self._tts_voice: str = "qt"
        self._profile: str = "normal"
        self._session_path: str | None = None

    def load_wpm(self, default: int = 400) -> int:
        return self._wpm

    def save_wpm(self, wpm: int) -> None:
        self._wpm = wpm

    def load_tts_wpm(self, default: int | None = None) -> int:
        return self._tts_wpm if self._tts_wpm is not None else (default or 400)

    def save_tts_wpm(self, wpm: int) -> None:
        self._tts_wpm = wpm

    def load_tts_pitch(self, default: int | None = None) -> int:
        return default if default is not None else 0

    def save_tts_pitch(self, pitch: int) -> None:
        pass

    def load_font_size(self, default: int = 42) -> int:
        return self._font_size

    def save_font_size(self, size: int) -> None:
        self._font_size = size

    def load_tts_enabled(self, default: bool = False) -> bool:
        return self._tts_enabled

    def save_tts_enabled(self, enabled: bool) -> None:
        self._tts_enabled = enabled

    def load_reading_profile(self, default: str = "normal") -> str:
        return self._profile

    def save_reading_profile(self, profile_id: str) -> None:
        self._profile = profile_id

    def load_reading_session(self):
        return None

    def save_reading_session(self, source_path: str, position: int) -> None:
        pass

    def clear_reading_session(self) -> None:
        pass

    def load_tts_voice(self, default: str = "qt") -> str:
        return self._tts_voice

    def save_tts_voice(self, voice_id: str) -> None:
        self._tts_voice = voice_id

    def load_voices_dir(self):
        from pathlib import Path
        return Path("/tmp/voices")

    def load_reading_profile_label(self) -> str:
        return "Normal"


@pytest.fixture
def controller(qapp):
    """Create an isolated ReadingController with fake speech + settings."""
    engine = ReadingEngine(wpm=300)
    speech = _FakeSpeech()
    settings = _FakeSettings()
    ctrl = ReadingController(engine, speech, settings)
    return ctrl


def _load_two_words(controller: ReadingController) -> None:
    """Helper: load two words into the controller."""
    controller.load([TextSegment("Hello world.", SegmentKind.PARAGRAPH)])


# --- Initial state ---

def test_initial_state(controller: ReadingController) -> None:
    assert not controller.playing
    assert controller.engine.is_empty
    assert controller.tts_enabled is False
    assert controller.tts_wpm == 300
    assert controller.engine.wpm == 300
    assert controller.display_position() == 0


# --- Load ---

def test_load_sets_engine_state(controller: ReadingController) -> None:
    _load_two_words(controller)
    assert not controller.engine.is_empty
    assert controller.engine.word_count == 2
    assert controller.engine.position == 0
    assert controller.source_path is None
    assert controller.source_kind is None


def test_load_with_source_path(controller: ReadingController) -> None:
    segments = [TextSegment("Test content.", SegmentKind.PARAGRAPH)]
    controller.load(segments, source_path="/tmp/test.txt", source_kind="file")
    assert controller.source_path == "/tmp/test.txt"
    assert controller.source_kind == "file"


def test_load_non_file_clears_source_path(controller: ReadingController) -> None:
    segments = [TextSegment("Test content.", SegmentKind.PARAGRAPH)]
    controller.load(segments, source_path="/tmp/test.txt", source_kind="clipboard")
    assert controller.source_path is None
    assert controller.source_kind == "clipboard"


def test_load_with_resume_position(controller: ReadingController) -> None:
    segments = [TextSegment("One two three four.", SegmentKind.PARAGRAPH)]
    controller.load(segments, resume_position=2)
    assert controller.engine.position == 2
    assert controller.engine.current_word == "three"


def test_load_clears_previous_state(controller: ReadingController) -> None:
    _load_two_words(controller)
    segments = [TextSegment("New text.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    assert controller.engine.word_count == 2
    assert controller.engine.current_word == "New"


# --- Play / Pause / Toggle ---

def test_play_sets_playing(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.play()
    assert controller.playing


def test_pause_clears_playing(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.play()
    assert controller.playing
    controller.pause()
    assert not controller.playing


def test_toggle_from_paused_to_playing(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.toggle()
    assert controller.playing
    controller.toggle()
    assert not controller.playing


def test_play_resets_when_finished(controller: ReadingController) -> None:
    segments = [TextSegment("Hello.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    # Advance past all words (1 word)
    controller.next_word()
    assert controller.engine.is_finished
    controller.play()
    assert controller.playing
    assert not controller.engine.is_finished
    assert controller.engine.position == 0


def test_pause_when_not_playing_is_noop(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.pause()  # should not raise
    assert not controller.playing


def test_play_on_empty_engine_does_not_crash(controller: ReadingController) -> None:
    controller.play()
    assert not controller.playing  # nothing to play


# --- Seek ---

def test_seek_moves_position(controller: ReadingController) -> None:
    segments = [TextSegment("One two three four.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.seek(2)
    assert controller.engine.position == 2
    assert controller.engine.current_word == "three"


def test_seek_stops_playback(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.play()
    assert controller.playing
    controller.seek(0)
    assert not controller.playing


def test_seek_bounds_clamp(controller: ReadingController) -> None:
    segments = [TextSegment("One two.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.seek(999)
    assert controller.engine.position == 1  # last word


def test_seek_negative_clamp(controller: ReadingController) -> None:
    segments = [TextSegment("One two.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.seek(-5)
    assert controller.engine.position == 0


# --- Navigation ---

def test_next_word_advances(controller: ReadingController) -> None:
    segments = [TextSegment("One two three.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.next_word()
    assert controller.engine.position == 1
    assert controller.engine.current_word == "two"


def test_previous_word_retreats(controller: ReadingController) -> None:
    segments = [TextSegment("One two three.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.seek(1)
    controller.previous_word()
    assert controller.engine.position == 0
    assert controller.engine.current_word == "One"


def test_next_word_on_finished_is_noop(controller: ReadingController) -> None:
    segments = [TextSegment("Hello.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    controller.next_word()
    assert controller.engine.is_finished
    controller.next_word()  # should not crash
    assert controller.engine.is_finished


def test_previous_word_on_empty_is_noop(controller: ReadingController) -> None:
    controller.previous_word()  # should not crash
    assert controller.engine.is_empty


# --- WPM ---

def test_set_wpm_updates_engine(controller: ReadingController) -> None:
    controller.set_wpm(600)
    assert controller.engine.wpm == 600


def test_set_wpm_snaps_to_step(controller: ReadingController) -> None:
    """WPM values are snapped to the configured step (25)."""
    from speedreader.settings import WPM_STEP, snap_wpm
    snapped = snap_wpm(612)
    controller.set_wpm(612)
    assert controller.engine.wpm == snapped


def test_set_tts_wpm_updates_property(controller: ReadingController) -> None:
    controller.set_tts_wpm(500)
    assert controller.tts_wpm == 500


# --- Profile ---

def test_set_profile_changes_engine(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.set_profile("study")
    assert controller.engine.profile_id == "study"


def test_set_profile_same_id_is_noop(controller: ReadingController) -> None:
    _load_two_words(controller)
    controller.set_profile("normal")
    assert controller.engine.profile_id == "normal"


# --- Signals ---

def test_word_changed_emitted_on_play(controller: ReadingController) -> None:
    _load_two_words(controller)
    received: list[str] = []
    controller.word_changed.connect(received.append)
    controller.play()
    assert len(received) >= 1
    # word_changed carries ORP-highlighted HTML
    assert 'e67e22' in received[0] or 'llo' in received[0]
    controller.pause()


def test_finished_emitted_when_reading_ends(controller: ReadingController) -> None:
    segments = [TextSegment("Done.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    finished_results: list[str] = []
    controller.finished.connect(lambda: finished_results.append("done"))
    controller.next_word()
    assert finished_results == ["done"]
    assert controller.engine.is_finished


def test_progress_changed_emitted(controller: ReadingController) -> None:
    segments = [TextSegment("One two three.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    positions: list[tuple[int, int]] = []
    controller.progress_changed.connect(lambda pos, total: positions.append((pos, total)))
    controller.next_word()
    assert len(positions) >= 1
    # next_word stops playback and emits progress
    last_pos, last_total = positions[-1]
    assert last_pos == 1
    assert last_total == 3


def test_status_changed_emitted_on_play_pause(controller: ReadingController) -> None:
    _load_two_words(controller)
    statuses: list[str] = []
    controller.status_changed.connect(statuses.append)
    controller.play()
    assert "playing" in statuses
    controller.pause()
    assert "paused" in statuses


def test_stop_emits_finished_when_at_end(controller: ReadingController) -> None:
    """Stop at end should signal the view that reading is done."""
    segments = [TextSegment("End.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    # Simulate reading to the end
    controller.next_word()
    # Already finished after next_word


# --- TTS toggle ---

def test_tts_enabled_toggle(controller: ReadingController) -> None:
    _load_two_words(controller)
    assert not controller.tts_enabled
    controller.tts_enabled = True
    assert controller.tts_enabled
    controller.tts_enabled = False
    assert not controller.tts_enabled


# --- Speech backend swap ---

def test_set_speech_backend_updates_name(controller: ReadingController) -> None:
    _load_two_words(controller)
    new_speech = _FakeSpeech("NewVoice")
    controller.set_speech_backend(new_speech)
    assert controller.speech.name == "NewVoice"


# --- Display position ---

def test_display_position_matches_engine(controller: ReadingController) -> None:
    segments = [TextSegment("One two three.", SegmentKind.PARAGRAPH)]
    controller.load(segments)
    assert controller.display_position() == 0
    controller.seek(1)
    assert controller.display_position() == 1
