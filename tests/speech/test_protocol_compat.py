"""All registered SpeechBackend implementations satisfy the protocol."""

from __future__ import annotations

import pytest

from speedreader.core.speech import SpeechBackend

pytest.importorskip("PySide6")


def test_qt_backend_satisfies_protocol(qapp) -> None:
    from speedreader.speech.qt_backend import QtSpeechBackend

    backend = QtSpeechBackend()
    # Duck-typed protocol check.
    assert hasattr(backend, "name")
    assert hasattr(backend, "capabilities")
    assert hasattr(backend, "set_rate_from_wpm")
    assert hasattr(backend, "set_finished_callback")
    assert hasattr(backend, "set_audio_started_callback")
    assert hasattr(backend, "speak")
    assert hasattr(backend, "stop")
    assert isinstance(backend.name, str)


def test_piper_backend_satisfies_protocol(qapp) -> None:
    pytest.importorskip("piper")
    from speedreader.speech.piper_backend import PiperSpeechBackend

    # Construct against a dummy model path; we don't synthesize here.
    backend = PiperSpeechBackend.__new__(PiperSpeechBackend)
    # We are not invoking __init__ (no model), but the attribute surface is
    # already defined on the class. Just verify the public names exist.
    for attr in (
        "name",
        "capabilities",
        "set_rate_from_wpm",
        "set_finished_callback",
        "set_audio_started_callback",
        "speak",
        "stop",
    ):
        assert hasattr(backend, attr) or hasattr(PiperSpeechBackend, attr)


def test_edge_backend_satisfies_protocol(qapp) -> None:
    pytest.importorskip("edge_tts")
    from speedreader.speech.web_edge_backend import EdgeTtsBackend

    backend = EdgeTtsBackend("es-ES-ElviraNeural")
    assert isinstance(backend.name, str)
    caps = backend.capabilities
    assert caps.phrase_sync is True


def test_azure_backend_satisfies_protocol(qapp, monkeypatch) -> None:
    pytest.importorskip("azure.cognitiveservices.speech")
    monkeypatch.setattr(
        "speedreader.speech.web_azure_backend.get_azure_key", lambda: "fake"
    )
    from speedreader.speech.web_azure_backend import AzureTtsBackend

    backend = AzureTtsBackend(
        voice_id="es-ES-ElviraNeural", region="eastus", subscription_key="fake"
    )
    assert isinstance(backend.name, str)
    caps = backend.capabilities
    assert caps.needs_key is True


def test_capabilities_dataclass_defaults() -> None:
    """Default SpeechCapabilities is conservative (no phrase sync)."""
    caps = SpeechBackend.__class__  # avoid unused warning  # noqa: F841
    from speedreader.core.speech import SpeechCapabilities

    caps = SpeechCapabilities()
    assert caps.phrase_sync is False
    assert caps.streaming is False
    assert caps.needs_key is False
    assert caps.max_chars_per_speak is None