"""Pitch capability advertisement across all SpeechBackend implementations."""

from __future__ import annotations

import pytest

from speedreader.core.rate import MAX_PITCH_PCT, MIN_PITCH_PCT, clamp_pitch_pct


# --- Pure helper checks (no Qt / network deps) ---


def test_clamp_pitch_pct_bounds() -> None:
    assert clamp_pitch_pct(100.0) == MAX_PITCH_PCT
    assert clamp_pitch_pct(-100.0) == MIN_PITCH_PCT
    assert clamp_pitch_pct(0.0) == 0.0
    assert clamp_pitch_pct(15.5) == 15.5


# --- Backend capability checks ---


def test_qt_backend_supports_pitch(qapp) -> None:
    """Qt QTextToSpeech supports pitch shifts."""
    from speedreader.speech.qt_backend import QtSpeechBackend

    backend = QtSpeechBackend()
    assert backend.capabilities.supports_pitch is True

    # Round-trip a few values through the setter / property.
    backend.set_pitch_from_pct(100.0)
    assert backend.pitch_pct == MAX_PITCH_PCT
    backend.set_pitch_from_pct(-50.0)
    assert backend.pitch_pct == -50.0
    backend.set_pitch_from_pct(0.0)
    assert backend.pitch_pct == 0.0


def test_edge_backend_supports_pitch(qapp) -> None:
    """Edge TTS supports pitch shifts."""
    pytest.importorskip("edge_tts")
    from speedreader.speech.web_edge_backend import EdgeTtsBackend

    backend = EdgeTtsBackend("es-ES-ElviraNeural")
    assert backend.capabilities.supports_pitch is True


def test_azure_backend_supports_pitch(qapp, monkeypatch) -> None:
    """Azure TTS supports pitch shifts (as SSML %)."""
    pytest.importorskip("azure.cognitiveservices.speech")
    monkeypatch.setattr(
        "speedreader.speech.web_azure_backend.get_azure_key", lambda: "fake-key"
    )
    from speedreader.speech.web_azure_backend import AzureTtsBackend

    backend = AzureTtsBackend(
        voice_id="es-ES-ElviraNeural",
        region="eastus",
        subscription_key="fake-key",
    )
    assert backend.capabilities.supports_pitch is True


def test_piper_backend_does_not_support_pitch() -> None:
    """Piper ignores pitch; capabilities must advertise it as unsupported."""
    pytest.importorskip("piper")
    from speedreader.speech.piper_backend import PiperSpeechBackend

    # PiperSpeechBackend.__init__ requires a real ONNX model path, so we skip
    # construction and just check the capabilities advertised on the class.
    backend = PiperSpeechBackend.__new__(PiperSpeechBackend)
    assert backend.capabilities.supports_pitch is False
