"""RSVP reading engine that steps through tokenized words."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from speedreader.domain import TextSegment

_WORD_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True)
class WordToken:
    """A single word in the reading queue."""

    text: str
    segment_index: int


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

    def interval_ms(self) -> int:
        """Milliseconds to wait between words at the current WPM."""
        return int(60_000 / self._wpm)


def tokenize_segments(segments: List[TextSegment]) -> List[WordToken]:
    """Split segment content into non-whitespace word tokens."""
    words: List[WordToken] = []
    for segment_index, segment in enumerate(segments):
        for match in _WORD_PATTERN.finditer(segment.content):
            words.append(WordToken(text=match.group(), segment_index=segment_index))
    return words
