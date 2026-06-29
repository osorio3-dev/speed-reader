"""Piper neural TTS backend."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QObject, QTimer, Slot
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices

from speedreader.speech.rate import wpm_to_length_scale
from speedreader.speech.voices import resolve_piper_model


def find_voice_model(voices_dir: Path, voice_id: str | None = None) -> Optional[Path]:
    """Return a Piper model path for ``voice_id`` or the best available voice."""
    return resolve_piper_model(voices_dir, voice_id)


class PiperSpeechBackend(QObject):
    """Speak text with a local Piper ONNX voice."""

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
        self._generation = 0
        self._playback_generation = 0
        self._heard_active = False
        self._finished_emitted = False

    @property
    def name(self) -> str:
        return f"Piper ({self._model_path.stem})"

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        self._length_scale = wpm_to_length_scale(wpm, pace_multiplier=pace_multiplier)

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._finished_callback = callback

    def speak(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            self._schedule_finished()
            return

        self._cancel_playback()
        self._playback_generation = self._generation

        syn_config = self._SynthesisConfig(length_scale=self._length_scale)
        chunks = list(self._voice.synthesize(cleaned, syn_config=syn_config))
        if not chunks:
            self._schedule_finished()
            return

        audio = b"".join(chunk.audio_int16_bytes for chunk in chunks)
        sample_rate = chunks[0].sample_rate

        audio_format = QAudioFormat()
        audio_format.setSampleRate(sample_rate)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self._heard_active = False
        self._finished_emitted = False
        self._audio_buffer = QBuffer(self)
        self._audio_buffer.setData(QByteArray(audio))
        if not self._audio_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            self._teardown_playback()
            self._schedule_finished()
            return

        self._audio_sink = QAudioSink(QMediaDevices.defaultAudioOutput(), audio_format, self)
        self._audio_sink.stateChanged.connect(self._on_sink_state_changed)
        self._audio_sink.start(self._audio_buffer)

    def stop(self) -> None:
        self._cancel_playback()

    def _cancel_playback(self) -> None:
        self._generation += 1
        self._teardown_playback()

    def _teardown_playback(self) -> None:
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

    @Slot(QAudio.State)
    def _on_sink_state_changed(self, state: QAudio.State) -> None:
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
        if self._finished_callback is None:
            return
        QTimer.singleShot(0, self._finished_callback)
