"""AzureTtsBackend requires a key and advertises it."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("azure.cognitiveservices.speech")

from speedreader.speech.web_azure_backend import AzureTtsBackend  # noqa: E402


def test_azure_raises_without_key(monkeypatch) -> None:
    """If the keyring has no key, the backend must raise on construction."""
    # Force the helper to return None even if a real key is configured.
    monkeypatch.setattr(
        "speedreader.speech.web_azure_backend.get_azure_key", lambda: None
    )
    with pytest.raises(RuntimeError):
        AzureTtsBackend(voice_id="es-ES-ElviraNeural", region="eastus")


def test_azure_capabilities_advertise_key_requirement(monkeypatch) -> None:
    monkeypatch.setattr(
        "speedreader.speech.web_azure_backend.get_azure_key", lambda: "fake-key"
    )
    backend = AzureTtsBackend(
        voice_id="es-ES-ElviraNeural", region="eastus", subscription_key="fake-key"
    )
    caps = backend.capabilities
    assert caps.needs_key is True
    assert caps.phrase_sync is True
    assert caps.streaming is True
    assert caps.max_chars_per_speak == 1000