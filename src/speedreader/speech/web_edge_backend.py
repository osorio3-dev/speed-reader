"""Microsoft Edge TTS web backend (no API key, free public endpoint).

V1 trade-offs
-------------
- The full MP3 stream from ``edge-tts`` is buffered in memory before playback.
  True streaming decode is left for v2; the latency floor is still 300-800 ms
  due to network + first-byte time, so buffering the whole phrase is
  acceptable for sentence-sized reads.
- Playback uses ``QMediaPlayer`` + ``QAudioOutput`` with a temporary MP3 file
  (``QSoundEffect`` cannot play from in-memory byte buffers). The temp file is
  deleted after playback completes.
- ``set_rate_from_wpm`` is a no-op: Edge voices do not expose a rate control
  in the free endpoint. WPM remains adjustable but maps to playback duration
  rather than the synthesizer rate.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Callable, Optional

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from speedreader.core.speech import SpeechBackend, SpeechCapabilities

logger = logging.getLogger(__name__)


class EdgeTtsBackend(QObject):
    """Speak text using ``edge-tts`` and a Qt media player.

    Signals
    -------
    _playback_finished : emitted on the main thread when QMediaPlayer reaches
        ``EndOfMedia``. Used internally to schedule the finished callback and
        clean up the temporary MP3 file.
    """

    _playback_finished = Signal()

    def __init__(self, voice_id: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._voice_id = voice_id
        self._finished_callback: Optional[Callable[[], None]] = None
        self._audio_started_callback: Optional[Callable[[], None]] = None

        # Lazily import edge-tts so the module loads even when offline.
        import edge_tts  # noqa: F401  (kept for import-side-effect detection)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

        self._temp_path: Optional[str] = None
        self._cancelled = False
        self._started_emitted = False

    @property
    def name(self) -> str:
        return f"Edge ({self._voice_id})"

    @property
    def capabilities(self) -> SpeechCapabilities:
        return SpeechCapabilities(
            phrase_sync=True,
            streaming=True,
            needs_key=False,
            max_chars_per_speak=2000,
        )

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        # Edge TTS has no rate control in the public endpoint. Intentionally a
        # no-op so the WPM slider still feels responsive to the user but does
        # not affect synthesis speed.
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
        # Network call is synchronous to keep the worker thread model simple;
        # edge-tts Communicate().stream() yields MP3 chunks we buffer.
        try:
            import asyncio

            from edge_tts import Communicate

            async def _collect() -> bytes:
                buf = bytearray()
                comm = Communicate(cleaned, voice=self._voice_id)
                async for chunk in comm.stream():
                    if self._cancelled:
                        break
                    if chunk.get("type") == "audio":
                        buf.extend(chunk["data"])
                return bytes(buf)

            mp3_bytes = asyncio.run(_collect())
        except Exception as exc:
            logger.debug("Edge TTS streaming failed: %s", exc)
            self._emit_finished()
            return

        if self._cancelled or not mp3_bytes:
            self._emit_finished()
            return

        tmp = tempfile.NamedTemporaryFile(
            prefix="speedreader-edge-", suffix=".mp3", delete=False
        )
        tmp.write(mp3_bytes)
        tmp.flush()
        tmp.close()
        self._temp_path = tmp.name

        self._player.setSource(QUrl.fromLocalFile(self._temp_path))
        self._player.play()

    def stop(self) -> None:
        self._cancelled = True
        self._player.stop()
        self._cleanup_temp()

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            if not self._started_emitted and self._audio_started_callback is not None:
                self._started_emitted = True
                self._audio_started_callback()

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state != QMediaPlayer.PlaybackState.StoppedState:
            return
        if self._cancelled:
            return
        self._cleanup_temp()
        self._emit_finished()

    def _cleanup_temp(self) -> None:
        if self._temp_path is None:
            return
        try:
            os.unlink(self._temp_path)
        except OSError:
            pass
        self._temp_path = None

    def _emit_finished(self) -> None:
        if self._finished_callback is None:
            return
        self._finished_callback()

    @Slot()
    def _on_internal_finished(self) -> None:  # pragma: no cover - signal trampoline
        self._emit_finished()