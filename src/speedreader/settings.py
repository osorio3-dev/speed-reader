"""Persistent user preferences."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSettings

from speedreader.engine import DEFAULT_WPM

MIN_WPM = 100
MAX_WPM = 1000
_WPM_KEY = "wpm"


def clamp_wpm(value: object, fallback: int = DEFAULT_WPM) -> int:
    """Clamp ``value`` to the supported WPM range."""
    try:
        wpm = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback
    return max(MIN_WPM, min(MAX_WPM, wpm))


class SettingsStore:
    """Load and save speedreader preferences."""

    def __init__(self, settings: Optional[QSettings] = None) -> None:
        self._settings = settings or QSettings("speedreader", "speedreader")

    def load_wpm(self, default: int = DEFAULT_WPM) -> int:
        """Return the saved WPM or ``default``."""
        return clamp_wpm(self._settings.value(_WPM_KEY, default), default)

    def save_wpm(self, wpm: int) -> None:
        """Persist the current WPM."""
        self._settings.setValue(_WPM_KEY, clamp_wpm(wpm))
