"""Tests for PiperWorker threading and PiperSpeechBackend off-thread synthesis.

Mocks PiperVoice to verify the worker emits audio_ready and that abort
cancels in-flight synthesis.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtTest import QTest

from speedreader.speech.piper_backend import PiperSpeechBackend, PiperWorker


# ---------------------------------------------------------------------------
# PiperWorker unit tests (direct calls, no thread)
# ---------------------------------------------------------------------------


class TestPiperWorker:
    """PiperWorker behaves correctly when synthesizing off the main thread."""

    def _make_mock_chunk(self, data: bytes = b"\x00\x01", sample_rate: int = 22050):
        chunk = MagicMock()
        chunk.audio_int16_bytes = data
        chunk.sample_rate = sample_rate
        return chunk

    def test_worker_emits_audio_ready_with_concatenated_audio(self):
        """do_synthesize emits audio_ready once with combined chunk data."""
        mock_voice = MagicMock()
        mock_voice.synthesize.return_value = [
            self._make_mock_chunk(b"\x00\x01"),
            self._make_mock_chunk(b"\x02\x03"),
        ]

        worker = PiperWorker(mock_voice)
        received: list[tuple[bytes, int, int]] = []

        def on_audio_ready(audio: QByteArray, sr: int, gen: int) -> None:
            received.append((bytes(audio), sr, gen))

        worker.audio_ready.connect(on_audio_ready)

        worker.do_synthesize("hello", 1.0, 42)

        assert len(received) == 1
        audio_bytes, sample_rate, generation = received[0]
        assert audio_bytes == b"\x00\x01\x02\x03"
        assert sample_rate == 22050
        assert generation == 42

    def test_empty_synthesis_emits_nothing(self):
        """No chunks from the voice -> no audio_ready emission."""
        mock_voice = MagicMock()
        mock_voice.synthesize.return_value = []

        worker = PiperWorker(mock_voice)
        received: list = []
        worker.audio_ready.connect(lambda *a: received.append(a))

        worker.do_synthesize("", 1.0, 1)

        assert len(received) == 0

    def test_new_synthesis_resets_abort_flag(self):
        """do_synthesize resets the abort flag so a fresh call works after abort."""
        mock_voice = MagicMock()
        mock_voice.synthesize.return_value = [
            self._make_mock_chunk(b"\x00\x01"),
        ]

        worker = PiperWorker(mock_voice)
        received: list = []
        worker.audio_ready.connect(lambda *a: received.append(a))

        worker.abort()
        worker.do_synthesize("hello", 1.0, 1)

        assert len(received) == 1  # do_synthesize resets _aborted = False

    def test_abort_during_multi_chunk_synthesis_halts(self):
        """Abort between chunks prevents audio_ready (mid-stream abort)."""
        mock_voice = MagicMock()

        chunks_yielded = 0

        def synthesize(*args, **kwargs):
            nonlocal chunks_yielded
            chunk = self._make_mock_chunk(b"\x00\x01")
            yield chunk
            chunks_yielded += 1
            # Simulate abort happening on the main thread
            worker.abort()
            yield chunk  # second chunk -- should be skipped
            chunks_yielded += 1

        mock_voice.synthesize = synthesize

        worker = PiperWorker(mock_voice)
        received: list = []
        worker.audio_ready.connect(lambda *a: received.append(a))

        worker.do_synthesize("hello", 1.0, 1)

        assert chunks_yielded == 1  # only first chunk yielded
        assert len(received) == 0  # no audio_ready emitted


# ---------------------------------------------------------------------------
# PiperSpeechBackend integration tests (with QThread)
# ---------------------------------------------------------------------------


class TestPiperSpeechBackendThreading:
    """PiperSpeechBackend delegates synthesis to a worker thread."""

    @patch("piper.PiperVoice")
    def test_backend_creates_thread_and_worker(self, MockPiperVoice, qapp):
        """__init__ creates a running QThread with a worker."""
        mock_voice_instance = MagicMock()
        MockPiperVoice.load.return_value = mock_voice_instance

        backend = PiperSpeechBackend(Path("/fake/model"))
        try:
            assert backend._thread is not None
            assert backend._thread.isRunning()
            assert backend._worker is not None
            assert backend._worker._voice is mock_voice_instance
        finally:
            backend._cleanup_thread()

    @patch("piper.PiperVoice")
    def test_speak_emits_queued_signal(self, MockPiperVoice, qapp):
        """speak() triggers do_synthesize on the worker thread via signal."""
        mock_voice_instance = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.audio_int16_bytes = b"\xca\xfe"
        mock_chunk.sample_rate = 16000
        mock_voice_instance.synthesize.return_value = [mock_chunk]
        MockPiperVoice.load.return_value = mock_voice_instance

        backend = PiperSpeechBackend(Path("/fake/model"))
        received: list = []

        def on_audio_ready(*args):
            received.append(args)

        backend._worker.audio_ready.connect(on_audio_ready)

        try:
            backend.speak("hello world")

            # Process events so the queued signal fires and worker runs.
            # Use a poll loop to avoid races with the worker thread.
            for _ in range(20):
                if received:
                    break
                QTest.qWait(100)

            assert len(received) == 1, f"Expected 1, got {len(received)} after 2s"
            audio, sr, gen = received[0]
            assert isinstance(audio, QByteArray)
            assert bytes(audio) == b"\xca\xfe"
            assert sr == 16000
            assert gen > 0
        finally:
            backend._cleanup_thread()

    @patch("piper.PiperVoice")
    def test_stop_increments_generation(self, MockPiperVoice, qapp):
        """stop() bumps generation so stale audio_ready is discarded."""
        mock_voice_instance = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.audio_int16_bytes = b"\xca\xfe"
        mock_chunk.sample_rate = 16000
        mock_voice_instance.synthesize.return_value = [mock_chunk]
        MockPiperVoice.load.return_value = mock_voice_instance

        backend = PiperSpeechBackend(Path("/fake/model"))
        received: list = []
        backend._worker.audio_ready.connect(lambda *a: received.append(a))

        try:
            gen_before = backend._generation

            backend.speak("hello")
            backend.stop()

            QTest.qWait(300)

            # Generation incremented by both speak (via _cancel_playback) and stop
            assert backend._generation >= gen_before + 2
        finally:
            backend._cleanup_thread()
