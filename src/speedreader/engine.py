"""RSVP reading engine that steps through tokenized words."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from speedreader.domain import SegmentKind, TextSegment

_WORD_PATTERN = re.compile(r"\S+")

_PUNCTUATION_PAUSE_MULTIPLIERS = {
    ".": 2.5,
    "!": 2.5,
    "?": 2.5,
    ",": 1.5,
    ";": 1.5,
    ":": 1.5,
    "…": 2.0,
}
_ELLIPSIS_PAUSE_MULTIPLIER = 2.0
_TRAILING_WRAPPERS = "\"')]}>"

_SEGMENT_PACE_MULTIPLIERS: dict[SegmentKind, float] = {
    SegmentKind.HEADING: 1.3,
    SegmentKind.PARAGRAPH: 1.0,
    SegmentKind.LIST_ITEM: 1.15,
    SegmentKind.CODE_BLOCK: 1.6,
    SegmentKind.CODE_INLINE: 1.2,
    SegmentKind.BLOCKQUOTE: 1.2,
}


@dataclass(frozen=True)
class WordToken:
    """A single word in the reading queue."""

    text: str
    segment_index: int
    segment_kind: SegmentKind


DEFAULT_WPM = 400


class ReadingEngine:
    """Advance through words extracted from TextSegments at a given WPM."""

    def __init__(self, wpm: int = DEFAULT_WPM) -> None:
        self._wpm = max(1, wpm)
        self._words: List[WordToken] = []
        self._position = 0

    @property
    def wpm(self) -> int:
        return self._wpm

    @wpm.setter
    def wpm(self, value: int) -> None:
        self._wpm = max(1, value)

    @property
    def position(self) -> int:
        return self._position

    @property
    def word_count(self) -> int:
        return len(self._words)

    @property
    def is_empty(self) -> bool:
        return not self._words

    @property
    def is_finished(self) -> bool:
        return self._position >= len(self._words)

    @property
    def current_word(self) -> Optional[str]:
        if self.is_finished:
            return None
        return self._words[self._position].text

    def load(self, segments: List[TextSegment]) -> None:
        """Replace the reading queue with words from the given segments."""
        self._words = tokenize_segments(segments)
        self._position = 0

    def reset(self) -> None:
        """Return to the first word without clearing loaded text."""
        self._position = 0

    def advance(self) -> Optional[str]:
        """Move to the next word and return the word now on screen."""
        if self.is_finished:
            return None
        word = self._words[self._position].text
        self._position += 1
        return word

    def retreat(self) -> Optional[str]:
        """Move to the previous word."""
        if not self._words:
            return None
        if self.is_finished:
            self._position = len(self._words) - 1
            return self.current_word
        if self._position <= 0:
            return self.current_word
        self._position -= 1
        return self.current_word

    def seek(self, index: int) -> None:
        """Jump to a word by its zero-based index."""
        if not self._words:
            self._position = 0
            return
        self._position = max(0, min(index, len(self._words) - 1))

    def interval_ms(self) -> int:
        """Milliseconds to display the current word at the current WPM."""
        base = int(60_000 / self._wpm)
        token = self._current_token()
        if token is None:
            return base
        multiplier = punctuation_pause_multiplier(
            token.text
        ) * segment_pace_multiplier(token.segment_kind)
        return int(base * multiplier)

    def _current_token(self) -> Optional[WordToken]:
        if self.is_finished:
            return None
        return self._words[self._position]


def punctuation_pause_multiplier(word: str) -> float:
    """Return a delay multiplier based on trailing punctuation."""
    stripped = word.rstrip(_TRAILING_WRAPPERS)
    if not stripped:
        return 1.0
    if stripped.endswith("..."):
        return _ELLIPSIS_PAUSE_MULTIPLIER
    return _PUNCTUATION_PAUSE_MULTIPLIERS.get(stripped[-1], 1.0)


def segment_pace_multiplier(kind: SegmentKind) -> float:
    """Return a delay multiplier for the segment kind of the current word."""
    return _SEGMENT_PACE_MULTIPLIERS.get(kind, 1.0)


def tokenize_segments(segments: List[TextSegment]) -> List[WordToken]:
    """Split segment content into non-whitespace word tokens."""
    words: List[WordToken] = []
    for segment_index, segment in enumerate(segments):
        for match in _WORD_PATTERN.finditer(segment.content):
            words.append(
                WordToken(
                    text=match.group(),
                    segment_index=segment_index,
                    segment_kind=segment.kind,
                )
            )
    return words
