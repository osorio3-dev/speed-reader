"""Speedreader core — zero-Qt reading domain models and logic."""

from speedreader.core.domain import SegmentKind, TextSegment
from speedreader.core.engine import ReadingEngine
from speedreader.core.orp import format_word_with_orp, optimal_recognition_index
from speedreader.core.profiles import (
    READING_PROFILES,
    ReadingProfile,
    normalize_profile_id,
    profile_label,
    tts_pace_multiplier,
    visual_pace_multiplier,
)

__all__ = [
    "SegmentKind",
    "TextSegment",
    "ReadingEngine",
    "format_word_with_orp",
    "optimal_recognition_index",
    "READING_PROFILES",
    "ReadingProfile",
    "normalize_profile_id",
    "profile_label",
    "tts_pace_multiplier",
    "visual_pace_multiplier",
]
