"""Helpers mapping WPM to speech engine parameters."""

DEFAULT_BASE_WPM = 300


def wpm_to_qt_rate(
    wpm: int,
    base_wpm: int = DEFAULT_BASE_WPM,
    pace_multiplier: float = 1.0,
) -> float:
    """Map WPM to QTextToSpeech rate in [-1.0, 1.0]."""
    effective_wpm = wpm / max(pace_multiplier, 0.1)
    return max(-1.0, min(1.0, (effective_wpm - base_wpm) / base_wpm))


def wpm_to_length_scale(
    wpm: int,
    base_wpm: int = DEFAULT_BASE_WPM,
    pace_multiplier: float = 1.0,
) -> float:
    """Map WPM to Piper ``length_scale`` (lower is faster)."""
    effective_wpm = wpm / max(pace_multiplier, 0.1)
    return base_wpm / max(effective_wpm, 1)
