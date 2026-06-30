"""Protocol definitions for speedreader core — zero Qt imports."""

from __future__ import annotations

from typing import Optional, Protocol


class SettingsProtocol(Protocol):
    """Persistence interface for speedreader preferences.

    All methods accept and return plain Python types (no Qt types).
    """

    def load_wpm(self, default: int = 400) -> int:
        """Return the saved WPM or ``default``."""
        ...

    def save_wpm(self, wpm: int) -> None:
        """Persist the current WPM."""
        ...

    def load_tts_wpm(self, default: int | None = None) -> int:
        """Return the saved TTS WPM or ``default`` (falls back to load_wpm)."""
        ...

    def save_tts_wpm(self, wpm: int) -> None:
        """Persist the TTS speaking WPM."""
        ...

    def load_font_size(self, default: int = 42) -> int:
        """Return the saved RSVP font size or ``default``."""
        ...

    def save_font_size(self, size: int) -> None:
        """Persist the RSVP font size."""
        ...

    def load_tts_enabled(self, default: bool = False) -> bool:
        """Return whether TTS-driven reading is enabled."""
        ...

    def save_tts_enabled(self, enabled: bool) -> None:
        """Persist the TTS enabled flag."""
        ...

    def load_reading_profile(self, default: str = "normal") -> str:
        """Return the saved reading profile id."""
        ...

    def save_reading_profile(self, profile_id: str) -> None:
        """Persist the reading profile id."""
        ...

    def load_reading_session(self) -> object:
        """Return the last saved reading session, or None."""
        ...

    def save_reading_session(self, source_path: str, position: int) -> None:
        """Persist a resumable file reading session."""
        ...

    def clear_reading_session(self) -> None:
        """Remove any saved reading session."""
        ...


class ClipboardProtocol(Protocol):
    """Minimal interface expected from a clipboard object."""

    def text(self) -> str:
        """Return the current clipboard text."""
        ...
