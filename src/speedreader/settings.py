"""Persistent user preferences."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings

from speedreader.engine import DEFAULT_WPM

MIN_WPM = 100
MAX_WPM = 1000
_WPM_KEY = "wpm"
_SESSION_SOURCE_KIND_KEY = "session/source_kind"
_SESSION_SOURCE_PATH_KEY = "session/source_path"
_SESSION_POSITION_KEY = "session/position"
_FILE_SOURCE_KIND = "file"


@dataclass(frozen=True)
class ReadingSession:
    """A resumable file reading session."""

    source_path: str
    position: int


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

    def load_reading_session(self) -> Optional[ReadingSession]:
        """Return the last saved file session if it is still valid."""
        if self._settings.value(_SESSION_SOURCE_KIND_KEY, "") != _FILE_SOURCE_KIND:
            return None

        source_path = self._settings.value(_SESSION_SOURCE_PATH_KEY, "")
        if not source_path or not Path(source_path).is_file():
            return None

        try:
            position = int(self._settings.value(_SESSION_POSITION_KEY, 0))
        except (TypeError, ValueError):
            position = 0

        return ReadingSession(source_path=source_path, position=max(position, 0))

    def save_reading_session(self, source_path: str, position: int) -> None:
        """Persist a resumable file reading session."""
        self._settings.setValue(_SESSION_SOURCE_KIND_KEY, _FILE_SOURCE_KIND)
        self._settings.setValue(_SESSION_SOURCE_PATH_KEY, source_path)
        self._settings.setValue(_SESSION_POSITION_KEY, max(position, 0))

    def clear_reading_session(self) -> None:
        """Remove any saved reading session."""
        self._settings.remove(_SESSION_SOURCE_KIND_KEY)
        self._settings.remove(_SESSION_SOURCE_PATH_KEY)
        self._settings.remove(_SESSION_POSITION_KEY)
