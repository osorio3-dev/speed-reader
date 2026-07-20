"""Speech backend protocol — zero Qt imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Protocol


@dataclass(frozen=True)
class SpeechCapabilities:
    """Declarative capabilities advertised by a SpeechBackend.

    phrase_sync
        Backend handles multi-word phrases (Piper, Azure). The controller
        advances one phrase at a time instead of one word at a time.
    streaming
        Backend can stream audio chunks incrementally.
    needs_key
        Backend requires API key configuration (Azure).
    max_chars_per_speak
        Optional character cap per speak() call. ``None`` for unlimited.
    supports_pitch
        Backend can shift pitch for the next utterance.
    """

    phrase_sync: bool = False
    streaming: bool = False
    needs_key: bool = False
    max_chars_per_speak: Optional[int] = None
    supports_pitch: bool = False


class SpeechBackend(Protocol):
    """Backend for text-to-speech.

    Implementations may be local (Piper, Qt) or network (Edge, Azure).
    """

    @property
    def name(self) -> str:
        """Human-readable backend name."""

    @property
    def capabilities(self) -> SpeechCapabilities:
        """Return the backend's static capability flags."""

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        """Configure speaking speed from the reader WPM slider."""

    def set_pitch_from_pct(self, pitch_pct: float) -> None:
        """Configure relative pitch (-50..+50 %) for the next utterance."""

    @property
    def pitch_pct(self) -> float:
        """Current pitch setting, -50..+50."""

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """Register a callback invoked after each utterance finishes."""

    def set_audio_started_callback(
        self, callback: Optional[Callable[[], None]]
    ) -> None:
        """Register a callback invoked when the backend starts producing audio.

        Optional. Backends that can detect first-audio latency should fire this
        on the main thread; backends that cannot may simply fire it right after
        ``speak()`` is invoked. Default implementations may treat this as a
        no-op when no callback is registered.
        """

    def speak(self, text: str) -> None:
        """Speak ``text`` and invoke the finished callback when done."""

    def stop(self) -> None:
        """Stop the current utterance immediately."""