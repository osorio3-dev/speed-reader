"""Reading pace profiles for visual RSVP and TTS."""

from __future__ import annotations

from dataclasses import dataclass

from speedreader.core.domain import SegmentKind

DEFAULT_PROFILE_ID = "normal"

_DEFAULT_VISUAL = {
    SegmentKind.HEADING: 1.3,
    SegmentKind.PARAGRAPH: 1.0,
    SegmentKind.LIST_ITEM: 1.15,
    SegmentKind.CODE_BLOCK: 1.6,
    SegmentKind.CODE_INLINE: 1.2,
    SegmentKind.BLOCKQUOTE: 1.2,
}

_DEFAULT_TTS = {
    SegmentKind.HEADING: 1.15,
    SegmentKind.PARAGRAPH: 1.0,
    SegmentKind.LIST_ITEM: 1.08,
    SegmentKind.CODE_BLOCK: 1.0,
    SegmentKind.CODE_INLINE: 1.05,
    SegmentKind.BLOCKQUOTE: 1.1,
}


@dataclass(frozen=True)
class ReadingProfile:
    """Named multipliers for visual and spoken pacing."""

    id: str
    label: str
    visual: dict[SegmentKind, float]
    tts: dict[SegmentKind, float]


READING_PROFILES: dict[str, ReadingProfile] = {
    "normal": ReadingProfile(
        id="normal",
        label="Normal",
        visual=dict(_DEFAULT_VISUAL),
        tts=dict(_DEFAULT_TTS),
    ),
    "study": ReadingProfile(
        id="study",
        label="Estudio",
        visual={
            **_DEFAULT_VISUAL,
            SegmentKind.HEADING: 1.5,
            SegmentKind.PARAGRAPH: 1.15,
            SegmentKind.BLOCKQUOTE: 1.35,
        },
        tts={
            **_DEFAULT_TTS,
            SegmentKind.HEADING: 1.25,
            SegmentKind.PARAGRAPH: 1.1,
            SegmentKind.BLOCKQUOTE: 1.2,
        },
    ),
    "technical": ReadingProfile(
        id="technical",
        label="Técnico",
        visual={
            **_DEFAULT_VISUAL,
            SegmentKind.HEADING: 1.2,
            SegmentKind.PARAGRAPH: 1.05,
            SegmentKind.CODE_BLOCK: 2.0,
            SegmentKind.CODE_INLINE: 1.5,
        },
        tts={
            **_DEFAULT_TTS,
            SegmentKind.HEADING: 1.1,
            SegmentKind.PARAGRAPH: 1.05,
            SegmentKind.CODE_BLOCK: 1.0,
            SegmentKind.CODE_INLINE: 1.15,
        },
    ),
}


def normalize_profile_id(profile_id: str) -> str:
    """Return a supported profile id."""
    if profile_id in READING_PROFILES:
        return profile_id
    return DEFAULT_PROFILE_ID


def profile_label(profile_id: str) -> str:
    """Return the display label for a profile."""
    return READING_PROFILES[normalize_profile_id(profile_id)].label


def visual_pace_multiplier(profile_id: str, kind: SegmentKind) -> float:
    """Return the visual RSVP multiplier for a segment kind."""
    profile = READING_PROFILES[normalize_profile_id(profile_id)]
    return profile.visual.get(kind, 1.0)


def tts_pace_multiplier(profile_id: str, kind: SegmentKind) -> float:
    """Return the TTS pace multiplier for a segment kind."""
    profile = READING_PROFILES[normalize_profile_id(profile_id)]
    return profile.tts.get(kind, 1.0)
