"""Piper neural TTS backend with threaded synthesis.

Architecture
------------
PiperSpeechBackend
    Owns a QThread and PiperWorker.  speak() emits a queued signal to the
    worker so that ONNX inference runs off the main thread.  A generation
    counter discards audio_ready replies that belong to cancelled utterances.

PiperWorker(QObject)
    Lives in the worker thread.  Receives do_synthesize(text, length_scale, gen),
    calls PiperVoice.synthesize(), and emits audio_ready(QByteArray, sample_rate, gen)
    back to the main thread.  abort() sets a flag checked between chunks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import (
    QByteArray,
    QBuffer,
    QIODevice,
    QObject,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from speedreader.speech.rate import wpm_to_length_scale
from speedreader.speech.voices import resolve_piper_model


def find_voice_model(voices_dir: Path, voice_id: str | None = None) -> Optional[Path]:
    """Return a Piper model path for ``voice_id`` or the best available voice."""
    return resolve_piper_model(voices_dir, voice_id)


class PiperWorker(QObject):
    """Perform Piper ONNX synthesis on a worker thread.

    Signals
    -------
    audio_ready(QByteArray, int, int)
        Emitted on the worker thread (auto-queued to the main thread) when
        synthesis is complete.  Payload: (audio_bytes, sample_rate, generation).
    """

    audio_ready = Signal(QByteArray, int, int)  # audio_bytes, sample_rate, generation

    def __init__(self, voice, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._voice = voice
        self._aborted = False

    # ------------------------------------------------------------------
    # Slots (invoked on the worker thread via queued signal or directly)
    # ------------------------------------------------------------------

    @Slot()
    def abort(self) -> None:
        """Request cancellation of the current synthesis.

        Thread-safe: a simple bool write protected by the GIL.
        """
        self._aborted = True

    @Slot(str, float, int)
    def do_synthesize(self, text: str, length_scale: float, generation: int) -> None:
        """Synthesize *text* and emit ``audio_ready``.

        Iterates over Piper's chunk generator so that ``abort()`` can be
        honoured between chunks.
        """
        self._aborted = False
        from piper.config import SynthesisConfig

        syn_config = SynthesisConfig(length_scale=length_scale)
        chunks: list = []
        for chunk in self._voice.synthesize(text, syn_config=syn_config):
            if self._aborted:
                return
            chunks.append(chunk)

        if not chunks:
            return

        audio = b"".join(chunk.audio_int16_bytes for chunk in chunks)
        sample_rate = chunks[0].sample_rate
        self.audio_ready.emit(QByteArray(audio), sample_rate, generation)


class PiperSpeechBackend(QObject):
    """Speak text with a local Piper ONNX voice, synthesised off the main thread.

    Usage is identical to the synchronous predecessor — the ``SpeechBackend``
    protocol is unchanged.

    Signals
    -------
    _synthesize_request(str, float, int)
        Internal cross-thread signal connected to the worker's do_synthesize slot.
    """

    _synthesize_request = Signal(str, float, int)  # text, length_scale, generation

    def __init__(self, model_path: Path) -> None:
        super().__init__()
        from piper import PiperVoice
        from piper.config import SynthesisConfig

        self._SynthesisConfig = SynthesisConfig
        self._voice = PiperVoice.load(str(model_path))
        self._model_path = model_path
        self._finished_callback: Optional[Callable[[], None]] = None
        self._length_scale = 1.0
        self._audio_sink: Optional[QAudioSink] = None
        self._audio_buffer: Optional[QBuffer] = None
        # Generation counter (main thread only) – every speak/stop bumps it
        # so that stale audio_ready arrivals are discarded.
        self._generation = 0
        # The generation value that the *current* audio playback belongs to.
        self._playback_generation = 0
        self._heard_active = False
        self._finished_emitted = False

        # --- Threaded worker -------------------------------------------------
        self._thread = QThread(self)
        self._worker = PiperWorker(self._voice)
        self._worker.moveToThread(self._thread)
        self._worker.audio_ready.connect(self._on_audio_ready)
        # Cross-thread signal -> slot connection (auto-queued by Qt)
        self._synthesize_request.connect(self._worker.do_synthesize)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()

    # ------------------------------------------------------------------
    # Public API (SpeechBackend protocol)
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return f"Piper ({self._model_path.stem})"

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        self._length_scale = wpm_to_length_scale(wpm, pace_multiplier=pace_multiplier)

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._finished_callback = callback

    def speak(self, text: str) -> None:
        """Enqueue *text* for synthesis on the worker thread.

        Returns immediately.  The finished callback fires on the main thread
        once playback of the synthesised audio completes.
        """
        cleaned = text.strip()
        if not cleaned:
            self._schedule_finished()
            return

        self._cancel_playback()
        gen = self._generation
        self._playback_generation = gen
        # Queued cross-thread signal — the worker slot runs on its own thread.
        self._synthesize_request.emit(cleaned, self._length_scale, gen)

    def stop(self) -> None:
        """Stop current utterance and cancel any in-flight synthesis."""
        self._cancel_playback()
        # Direct call is safe here: abort() just sets a GIL-protected bool.
        self._worker.abort()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cancel_playback(self) -> None:
        """Invalidate the current generation and tear down audio playback."""
        self._generation += 1
        self._teardown_playback()

    def _teardown_playback(self) -> None:
        """Stop the audio sink and release buffers (main thread only)."""
        if self._audio_sink is not None:
            self._audio_sink.stateChanged.disconnect(self._on_sink_state_changed)
            self._audio_sink.stop()
            self._audio_sink.deleteLater()
            self._audio_sink = None
        if self._audio_buffer is not None:
            self._audio_buffer.close()
            self._audio_buffer.deleteLater()
            self._audio_buffer = None
        self._heard_active = False

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(QByteArray, int, int)
    def _on_audio_ready(
        self, audio_bytes: QByteArray, sample_rate: int, generation: int
    ) -> None:
        """Receive synthesised audio from the worker (main thread slot).

        If *generation* does not match the current ``_generation`` the audio
        is silently dropped (it belongs to a cancelled utterance).
        """
        if generation != self._generation:
            return  # stale

        audio_format = QAudioFormat()
        audio_format.setSampleRate(sample_rate)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self._heard_active = False
        self._finished_emitted = False
        self._audio_buffer = QBuffer(self)
        self._audio_buffer.setData(audio_bytes)
        if not self._audio_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            self._teardown_playback()
            self._schedule_finished()
            return

        self._audio_sink = QAudioSink(
            QMediaDevices.defaultAudioOutput(), audio_format, self
        )
        self._audio_sink.stateChanged.connect(self._on_sink_state_changed)
        self._audio_sink.start(self._audio_buffer)

    @Slot(QAudio.State)
    def _on_sink_state_changed(self, state: QAudio.State) -> None:
        """Track sink state and fire the finished callback when Idle is reached."""
        if self._playback_generation != self._generation:
            return
        if state == QAudio.State.ActiveState:
            self._heard_active = True
            return
        if state != QAudio.State.IdleState or not self._heard_active:
            return
        if self._finished_emitted:
            return

        self._finished_emitted = True
        self._teardown_playback()
        self._schedule_finished()

    def _schedule_finished(self) -> None:
        """Invoke the user-registered finished callback on the main thread."""
        if self._finished_callback is None:
            return
        QTimer.singleShot(0, self._finished_callback)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_thread(self) -> None:
        """Stop the worker thread and wait for it to finish."""
        if self._thread is None:
            return
        try:
            if self._thread.isRunning():
                self._worker.abort()
                self._thread.quit()
                self._thread.wait(1000)
        except (RuntimeError, AttributeError):
            # C++ object may already be deleted during interpreter shutdown
            pass

    def __del__(self) -> None:
        self._cleanup_thread()
