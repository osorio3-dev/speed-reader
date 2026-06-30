"""Helpers mapping WPM to speech engine parameters — zero Qt imports."""

DEFAULT_BASE_WPM = 300
MIN_PIPER_LENGTH_SCALE = 0.15


def wpm_to_qt_rate(
    wpm: int,
    base_wpm: int = DEFAULT_BASE_WPM,
    pace_multiplier: float = 1.0,
) -> float:
    """Map WPM to QTextToSpeech rate in [-1.0, 1.0]."""
    effective_wpm = wpm / max(pace_multiplier, 0.1)
    # Qt caps at 1.0; compress the curve so high WPM still maps usefully.
    fast_anchor = base_wpm * 2
    return max(-1.0, min(1.0, (effective_wpm - base_wpm) / fast_anchor))


def wpm_to_length_scale(
    wpm: int,
    base_wpm: int = DEFAULT_BASE_WPM,
    pace_multiplier: float = 1.0,
) -> float:
    """Map WPM to Piper ``length_scale`` (lower is faster)."""
    effective_wpm = wpm / max(pace_multiplier, 0.1)
    scale = base_wpm / max(effective_wpm, 1)
    return max(MIN_PIPER_LENGTH_SCALE, scale)
