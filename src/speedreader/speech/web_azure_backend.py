"""Azure Cognitive Services Speech TTS backend.

Requires an Azure Speech subscription key. The key is fetched from
``keyring`` under service ``speedreader`` with username ``azure_key`` and the
region from ``azure_region`` (default ``eastus``).

V1 trade-offs
-------------
- Rate control is delegated to the Azure SDK; ``set_rate_from_wpm`` is a
  no-op because Azure prosody control requires SSML ``<prosody>`` which v1
  does not emit.
- A 1000-character per-call cap is enforced by splitting on sentence
  boundaries; long inputs are concatenated sequentially without joining
  audio.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Slot

from speedreader.core.speech import SpeechBackend, SpeechCapabilities
from speedreader.settings import get_azure_key

logger = logging.getLogger(__name__)

_MAX_CHARS = 1000


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _split_into_chunks(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    """Split text on sentence boundaries, never exceeding ``max_chars``."""
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return [cleaned]

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                # Hard-wrap very long single sentences on commas.
                parts = re.split(r"(?<=,)\s+", sentence)
                current = ""
                for part in parts:
                    if len(current) + len(part) + 1 <= max_chars:
                        current = f"{current} {part}".strip()
                    else:
                        if current:
                            chunks.append(current)
                        current = part[:max_chars]
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks


class AzureTtsBackend(QObject):
    """Speak text using Azure Cognitive Services Speech SDK.

    Signals
    -------
    _synthesis_done : emitted on the main thread when the queued chunks have
        all finished. Schedules the finished callback exactly once.
    """

    _synthesis_done = Signal()

    def __init__(
        self,
        voice_id: str,
        region: str,
        subscription_key: Optional[str] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        if subscription_key is None:
            subscription_key = get_azure_key()
        if subscription_key is None:
            raise RuntimeError("Azure key not configured")
        self._voice_id = voice_id
        self._region = region
        self._key = subscription_key
        self._finished_callback: Optional[Callable[[], None]] = None
        self._audio_started_callback: Optional[Callable[[], None]] = None

        import azure.cognitiveservices.speech as speechsdk  # type: ignore

        self._speechsdk = speechsdk
        self._lang = voice_id.split("-", 1)[0].lower() if "-" in voice_id else "es"
        self._speech_config = speechsdk.SpeechConfig(
            subscription=self._key, region=self._region
        )
        self._speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Ogg48Khz16BitMonoOpus
        )

        self._pending_chunks: list[str] = []
        self._current_task: Optional[object] = None
        self._cancelled = False
        self._started_emitted = False
        self._lock = threading.Lock()

        self._synthesis_done.connect(self._on_synthesis_done)

    @property
    def name(self) -> str:
        return f"Azure ({self._voice_id})"

    @property
    def capabilities(self) -> SpeechCapabilities:
        return SpeechCapabilities(
            phrase_sync=True,
            streaming=True,
            needs_key=True,
            max_chars_per_speak=_MAX_CHARS,
        )

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        # SSML prosody is out of scope for v1; documented above.
        return None

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._finished_callback = callback

    def set_audio_started_callback(
        self, callback: Optional[Callable[[], None]]
    ) -> None:
        self._audio_started_callback = callback

    def speak(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            self._emit_finished()
            return
        self.stop()
        self._cancelled = False
        self._started_emitted = False
        self._pending_chunks = _split_into_chunks(cleaned)
        self._synthesize_next()

    def stop(self) -> None:
        with self._lock:
            self._cancelled = True
            self._pending_chunks.clear()
            if self._current_task is not None:
                try:
                    self._current_task.stop()
                except Exception:
                    pass
                self._current_task = None

    def _synthesize_next(self) -> None:
        if self._cancelled:
            self._emit_finished()
            return
        if not self._pending_chunks:
            self._synthesis_done.emit()
            return
        chunk = self._pending_chunks.pop(0)
        ssml = (
            f'<speak version="1.0" xml:lang="{self._lang}">'
            f'<voice name="{_xml_escape(self._voice_id)}">'
            f"{_xml_escape(chunk)}"
            "</voice>"
            "</speak>"
        )

        try:
            synthesizer = self._speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config
            )

            def _on_synth(evt) -> None:  # pragma: no cover - SDK callback
                if self._cancelled:
                    return
                if not self._started_emitted:
                    self._started_emitted = True
                    if self._audio_started_callback is not None:
                        self._audio_started_callback()

            def _on_complete(evt) -> None:  # pragma: no cover - SDK callback
                self._synthesize_next()

            def _on_cancel(evt) -> None:  # pragma: no cover - SDK callback
                logger.debug("Azure synthesis cancelled: %s", evt)
                self._emit_finished()

            def _on_error(evt) -> None:  # pragma: no cover - SDK callback
                logger.debug("Azure synthesis error: %s", evt)
                self._emit_finished()

            synthesizer.synthesizing.connect(_on_synth)
            synthesizer.synthesis_completed.connect(_on_complete)
            synthesizer.synthesis_canceled.connect(_on_cancel)
            synthesizer.synthesis_error.connect(_on_error)
            self._current_task = synthesizer
            synthesizer.speak_ssml_async(ssml)
        except Exception as exc:
            logger.debug("Azure synthesis dispatch failed: %s", exc)
            self._emit_finished()

    @Slot()
    def _on_synthesis_done(self) -> None:
        if self._cancelled:
            return
        self._current_task = None
        self._emit_finished()

    def _emit_finished(self) -> None:
        if self._finished_callback is None:
            return
        self._finished_callback()