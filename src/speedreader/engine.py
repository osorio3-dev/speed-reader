"""RSVP reading engine that steps through tokenized words."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from speedreader.domain import SegmentKind, TextSegment
from speedreader.profiles import (
    DEFAULT_PROFILE_ID,
    normalize_profile_id,
    tts_pace_multiplier as profile_tts_pace_multiplier,
    visual_pace_multiplier,
)

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

@dataclass(frozen=True)
class WordToken:
    """A single word in the reading queue."""

    text: str
    segment_index: int
    segment_kind: SegmentKind


DEFAULT_WPM = 400


class ReadingEngine:
    """Advance through words extracted from TextSegments at a given WPM."""

    def __init__(self, wpm: int = DEFAULT_WPM, profile_id: str = DEFAULT_PROFILE_ID) -> None:
        self._wpm = max(1, wpm)
        self._profile_id = normalize_profile_id(profile_id)
        self._words: List[WordToken] = []
        self._position = 0

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def set_profile(self, profile_id: str) -> None:
        """Switch the active reading profile."""
        self._profile_id = normalize_profile_id(profile_id)

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

    @property
    def current_segment_kind(self) -> Optional[SegmentKind]:
        token = self._current_token()
        return token.segment_kind if token is not None else None

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
        return self.interval_ms_at(self._position)

    def interval_ms_at(self, index: int) -> int:
        """Milliseconds to display the word at ``index``."""
        base = int(60_000 / self._wpm)
        token = self.token_at(index)
        if token is None:
            return base
        multiplier = punctuation_pause_multiplier(
            token.text
        ) * visual_pace_multiplier(self._profile_id, token.segment_kind)
        return int(base * multiplier)

    def speech_pace_multiplier(self, index: Optional[int] = None) -> float:
        """Return the TTS pace multiplier for the word at ``index``."""
        token = self.token_at(self._position if index is None else index)
        if token is None:
            return 1.0
        return profile_tts_pace_multiplier(self._profile_id, token.segment_kind)

    def token_at(self, index: int) -> Optional[WordToken]:
        """Return the token at ``index`` if it exists."""
        if index < 0 or index >= len(self._words):
            return None
        return self._words[index]

    def phrase_end_position(self) -> int:
        """Return the index after the last word in the current phrase."""
        return phrase_end_index(self._words, self._position)

    def retreat_phrase(self) -> Optional[str]:
        """Move to the first word of the previous phrase."""
        if not self._words:
            return None
        anchor = self._position - 1 if self._position > 0 else 0
        if self.is_finished:
            anchor = len(self._words) - 1
        self._position = phrase_start_index(self._words, anchor)
        return self.current_word

    def advance_to_next_phrase(self) -> Optional[str]:
        """Move to the first word of the next phrase."""
        if self.is_finished or not self._words:
            return None
        end = phrase_end_index(self._words, self._position)
        self._position = min(end, len(self._words))
        if self.is_finished:
            return None
        return self.current_word

    def _current_token(self) -> Optional[WordToken]:
        if self.is_finished:
            return None
        return self._words[self._position]

    def current_phrase_text(self) -> Optional[str]:
        """Return the phrase starting at the current position."""
        if self.is_finished:
            return None
        end = phrase_end_index(self._words, self._position)
        words = self._words[self._position : end]
        if not words:
            return None
        return " ".join(word.text for word in words)

    def advance_phrase(self) -> Optional[str]:
        """Move to the first word after the current phrase."""
        if self.is_finished:
            return None
        end = phrase_end_index(self._words, self._position)
        phrase = " ".join(word.text for word in self._words[self._position : end])
        self._position = end
        return phrase or None


def phrase_start_index(words: List[WordToken], index: int) -> int:
    """Return the first word index of the phrase containing ``index``."""
    if not words:
        return 0
    anchor = max(0, min(index, len(words) - 1))
    position = 0
    while position < len(words):
        end = phrase_end_index(words, position)
        if position <= anchor < end:
            return position
        position = end
    return anchor


def phrase_end_index(words: List[WordToken], start: int) -> int:
    """Return the index after the last word in the phrase that begins at ``start``."""
    if start >= len(words):
        return start

    start_kind = words[start].segment_kind
    start_segment = words[start].segment_index
    if start_kind == SegmentKind.CODE_BLOCK:
        index = start
        while index < len(words) and words[index].segment_index == start_segment:
            index += 1
        return index

    index = start
    while index < len(words):
        token = words[index]
        if token.segment_kind == SegmentKind.CODE_BLOCK:
            return index
        if index > start and token.segment_index != start_segment:
            return index
        if ends_sentence(token.text):
            return index + 1
        index += 1
    return len(words)


def ends_sentence(word: str) -> bool:
    """Return True when ``word`` ends a sentence."""
    stripped = word.rstrip(_TRAILING_WRAPPERS)
    if not stripped:
        return False
    if stripped.endswith("..."):
        return True
    return stripped[-1] in ".!?"


def punctuation_pause_multiplier(word: str) -> float:
    """Return a delay multiplier based on trailing punctuation."""
    stripped = word.rstrip(_TRAILING_WRAPPERS)
    if not stripped:
        return 1.0
    if stripped.endswith("..."):
        return _ELLIPSIS_PAUSE_MULTIPLIER
    return _PUNCTUATION_PAUSE_MULTIPLIERS.get(stripped[-1], 1.0)


def segment_pace_multiplier(kind: SegmentKind) -> float:
    """Return the default visual pace multiplier for a segment kind."""
    return visual_pace_multiplier(DEFAULT_PROFILE_ID, kind)


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
