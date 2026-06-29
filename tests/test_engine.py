"""Tests for the RSVP reading engine."""

import pytest

from speedreader import ReadingEngine, SegmentKind, TextSegment
from speedreader.engine import tokenize_segments


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


def test_interval_ms_respects_wpm(engine: ReadingEngine) -> None:
    engine.wpm = 400
    assert engine.interval_ms() == 150
    engine.wpm = 600
    assert engine.interval_ms() == 100


def test_empty_load(engine: ReadingEngine) -> None:
    engine.load([])
    assert engine.is_empty
    assert engine.current_word is None
    assert engine.advance() is None
