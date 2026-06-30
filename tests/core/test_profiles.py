"""Tests for reading pace profiles."""

from speedreader.domain import SegmentKind
from speedreader.profiles import (
    READING_PROFILES,
    normalize_profile_id,
    tts_pace_multiplier,
    visual_pace_multiplier,
)


def test_normalize_profile_id_falls_back_to_normal() -> None:
    assert normalize_profile_id("unknown") == "normal"


def test_study_profile_slows_headings_more_than_normal() -> None:
    normal = visual_pace_multiplier("normal", SegmentKind.HEADING)
    study = visual_pace_multiplier("study", SegmentKind.HEADING)
    assert study > normal


def test_technical_profile_has_distinct_tts_code_inline_pace() -> None:
    normal = tts_pace_multiplier("normal", SegmentKind.CODE_INLINE)
    technical = tts_pace_multiplier("technical", SegmentKind.CODE_INLINE)
    assert technical > normal


def test_all_profiles_have_labels() -> None:
    for profile in READING_PROFILES.values():
        assert profile.label
        assert profile.id in READING_PROFILES
