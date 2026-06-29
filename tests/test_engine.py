"""Tests for the RSVP reading engine."""

import pytest

from speedreader import ReadingEngine, SegmentKind, TextSegment
from speedreader.engine import (
    punctuation_pause_multiplier,
    segment_pace_multiplier,
    tokenize_segments,
)


@pytest.fixture
def engine() -> ReadingEngine:
    return ReadingEngine(wpm=300)


def test_tokenize_segments_splits_words() -> None:
    segments = [
        TextSegment(content="Hello world", kind=SegmentKind.PARAGRAPH),
        TextSegment(content="Second line here", kind=SegmentKind.PARAGRAPH),
    ]
    words = tokenize_segments(segments)
    assert [word.text for word in words] == ["Hello", "world", "Second", "line", "here"]
    assert [word.segment_index for word in words] == [0, 0, 1, 1, 1]
    assert all(word.segment_kind == SegmentKind.PARAGRAPH for word in words)


def test_tokenize_segments_preserves_segment_kind() -> None:
    segments = [
        TextSegment(content="Title", kind=SegmentKind.HEADING),
        TextSegment(content="print(x)", kind=SegmentKind.CODE_BLOCK),
    ]
    words = tokenize_segments(segments)
    assert words[0].segment_kind == SegmentKind.HEADING
    assert words[1].segment_kind == SegmentKind.CODE_BLOCK


def test_load_and_advance(engine: ReadingEngine) -> None:
    engine.load([TextSegment(content="one two three", kind=SegmentKind.PARAGRAPH)])
    assert engine.word_count == 3
    assert engine.current_word == "one"
    assert engine.advance() == "one"
    assert engine.current_word == "two"
    assert engine.advance() == "two"
    assert engine.current_word == "three"
    assert engine.advance() == "three"
    assert engine.is_finished
    assert engine.current_word is None


def test_reset_returns_to_start(engine: ReadingEngine) -> None:
    engine.load([TextSegment(content="alpha beta", kind=SegmentKind.PARAGRAPH)])
    engine.advance()
    engine.reset()
    assert engine.position == 0
    assert engine.current_word == "alpha"


def test_retreat_moves_back(engine: ReadingEngine) -> None:
    engine.load([TextSegment(content="one two three", kind=SegmentKind.PARAGRAPH)])
    engine.advance()
    engine.advance()
    assert engine.current_word == "three"
    engine.retreat()
    assert engine.current_word == "two"
    engine.retreat()
    assert engine.current_word == "one"
    engine.retreat()
    assert engine.current_word == "one"


def test_retreat_from_finished_shows_last_word(engine: ReadingEngine) -> None:
    engine.load([TextSegment(content="only", kind=SegmentKind.PARAGRAPH)])
    engine.advance()
    assert engine.is_finished
    engine.retreat()
    assert engine.current_word == "only"


def test_interval_ms_respects_wpm(engine: ReadingEngine) -> None:
    engine.wpm = 400
    assert engine.interval_ms() == 150
    engine.wpm = 600
    assert engine.interval_ms() == 100


def test_punctuation_pause_multiplier() -> None:
    assert punctuation_pause_multiplier("word") == 1.0
    assert punctuation_pause_multiplier("wait,") == 1.5
    assert punctuation_pause_multiplier("Done.") == 2.5
    assert punctuation_pause_multiplier("Really?") == 2.5
    assert punctuation_pause_multiplier("wait...") == 2.0


def test_interval_ms_applies_punctuation_pause(engine: ReadingEngine) -> None:
    engine.wpm = 300
    engine.load([TextSegment(content="Next, stop.", kind=SegmentKind.PARAGRAPH)])
    assert engine.current_word == "Next,"
    assert engine.interval_ms() == 300
    engine.advance()
    assert engine.current_word == "stop."
    assert engine.interval_ms() == 500


def test_segment_pace_multiplier() -> None:
    assert segment_pace_multiplier(SegmentKind.PARAGRAPH) == 1.0
    assert segment_pace_multiplier(SegmentKind.HEADING) == 1.3
    assert segment_pace_multiplier(SegmentKind.CODE_BLOCK) == 1.6


def test_interval_ms_applies_segment_pace(engine: ReadingEngine) -> None:
    engine.wpm = 300
    engine.load([TextSegment(content="Title", kind=SegmentKind.HEADING)])
    assert engine.interval_ms() == 260


def test_seek_jumps_to_word(engine: ReadingEngine) -> None:
    engine.load([TextSegment(content="one two three four", kind=SegmentKind.PARAGRAPH)])
    engine.seek(2)
    assert engine.current_word == "three"
    engine.seek(99)
    assert engine.current_word == "four"


def test_empty_load(engine: ReadingEngine) -> None:
    engine.load([])
    assert engine.is_empty
    assert engine.current_word is None
    assert engine.advance() is None
