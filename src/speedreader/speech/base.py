"""Speech backend protocol."""

from __future__ import annotations

from typing import Callable, Optional, Protocol


class SpeechBackend(Protocol):
    """Offline text-to-speech backend."""

    @property
    def name(self) -> str:
        """Human-readable backend name."""

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        """Configure speaking speed from the reader WPM slider."""

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """Register a callback invoked after each utterance finishes."""

    def speak(self, text: str) -> None:
        """Speak ``text`` and invoke the finished callback when done."""

    def stop(self) -> None:
        """Stop the current utterance immediately."""
