"""EdgeTtsBackend capabilities advertised correctly."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("edge_tts")

from speedreader.speech.web_edge_backend import EdgeTtsBackend  # noqa: E402


def test_edge_capabilities_shape() -> None:
    pytest.importorskip("PySide6.QtMultimedia")
    backend = EdgeTtsBackend("es-ES-ElviraNeural")
    caps = backend.capabilities
    assert caps.phrase_sync is True
    assert caps.streaming is True
    assert caps.needs_key is False
    assert caps.max_chars_per_speak == 2000


def test_edge_capabilities_dataclass_is_frozen() -> None:
    from speedreader.core.speech import SpeechCapabilities

    caps = SpeechCapabilities(
        phrase_sync=True, streaming=True, needs_key=False, max_chars_per_speak=2000
    )
    with pytest.raises(Exception):
        caps.needs_key = True  # type: ignore[misc]