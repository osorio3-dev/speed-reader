"""Create the best available speech backend (Piper, Edge, Azure, Qt).

Order of preference when ``preference='auto'`` and the caller did not name
a specific backend: explicit match -> piper -> edge -> azure -> qt.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional

from speedreader.core.speech import SpeechBackend
from speedreader.speech.qt_backend import QtSpeechBackend
from speedreader.speech.voices import (
    AZURE_VOICE_PREFIX,
    EDGE_PREFERRED_VOICES,
    EDGE_VOICE_PREFIX,
    QT_VOICE_ID,
    resolve_azure_voice,
    resolve_edge_voice,
    resolve_piper_model,
)

logger = logging.getLogger(__name__)

TtsBackendPreference = Literal["auto", "piper", "qt", "edge", "azure"]

DEFAULT_VOICES_DIR = Path.home() / ".local" / "share" / "speedreader" / "voices"


def create_speech_backend(
    preference: TtsBackendPreference = "auto",
    voices_dir: Optional[Path] = None,
    voice_id: Optional[str] = None,
) -> SpeechBackend:
    """Return the best available SpeechBackend for *voice_id*."""
    voices_path = voices_dir or DEFAULT_VOICES_DIR

    # Explicit voice-id prefixes always win over preference.
    if voice_id == QT_VOICE_ID:
        return QtSpeechBackend()
    if voice_id and voice_id.startswith(EDGE_VOICE_PREFIX):
        edge = _try_create_edge_backend(voice_id)
        if edge is not None:
            return edge
    if voice_id and voice_id.startswith(AZURE_VOICE_PREFIX):
        azure = _try_create_azure_backend(voice_id)
        if azure is not None:
            return azure

    if preference == "qt":
        return QtSpeechBackend()
    if preference == "piper":
        piper = _try_create_piper_backend(voices_path, voice_id)
        if piper is not None:
            return piper
        return QtSpeechBackend()
    if preference == "edge":
        edge = _try_create_edge_backend(voice_id)
        if edge is not None:
            return edge
        return QtSpeechBackend()
    if preference == "azure":
        azure = _try_create_azure_backend(voice_id)
        if azure is not None:
            return azure
        return QtSpeechBackend()

    # Auto: explicit match first, then network, then local.
    piper = _try_create_piper_backend(voices_path, voice_id)
    if piper is not None:
        return piper
    edge = _try_create_edge_backend(voice_id)
    if edge is not None:
        return edge
    azure = _try_create_azure_backend(voice_id)
    if azure is not None:
        return azure
    return QtSpeechBackend()


def _try_create_piper_backend(
    voices_dir: Path,
    voice_id: Optional[str] = None,
) -> Optional[SpeechBackend]:
    try:
        from speedreader.speech.piper_backend import PiperSpeechBackend
    except ImportError as exc:
        logger.debug("Piper backend unavailable: %s", exc)
        return None

    model_path = resolve_piper_model(voices_dir, voice_id)
    if model_path is None:
        logger.debug(
            "Piper backend unavailable: no model resolved (voices_dir=%s, voice_id=%s)",
            voices_dir,
            voice_id,
        )
        return None

    try:
        return PiperSpeechBackend(model_path)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Piper backend failed to construct: %s", exc)
        return None


def _try_create_edge_backend(
    voice_id: Optional[str] = None,
) -> Optional[SpeechBackend]:
    try:
        from speedreader.speech.web_edge_backend import EdgeTtsBackend
    except ImportError as exc:
        logger.debug("Edge backend unavailable: %s", exc)
        return None

    if voice_id is not None and not voice_id.startswith(EDGE_VOICE_PREFIX):
        resolved = resolve_edge_voice(voice_id)
        if resolved is None:
            logger.debug(
                "Edge backend unavailable: no voice resolved for %s", voice_id
            )
            return None
        target_voice = resolved
    else:
        target_voice = EDGE_PREFERRED_VOICES[0]

    try:
        return EdgeTtsBackend(target_voice)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Edge backend failed to construct: %s", exc)
        return None


def _try_create_azure_backend(
    voice_id: Optional[str] = None,
) -> Optional[SpeechBackend]:
    try:
        from speedreader.speech.web_azure_backend import AzureTtsBackend
    except ImportError as exc:
        logger.debug("Azure backend unavailable: %s", exc)
        return None

    resolved_voice = (
        resolve_azure_voice(voice_id) if voice_id else None
    )
    region = _azure_region_keyring()
    key = _azure_keyring_lookup()
    if key is None:
        logger.debug("Azure backend unavailable: no key configured in keyring")
        return None

    target_voice = resolved_voice or "es-ES-ElviraNeural"
    try:
        return AzureTtsBackend(voice_id=target_voice, region=region, subscription_key=key)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Azure backend failed to construct: %s", exc)
        return None


def _azure_keyring_lookup() -> Optional[str]:
    try:
        import keyring
    except ImportError:
        return None
    try:
        return keyring.get_password("speedreader", "azure_key")
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Azure keyring lookup failed: %s", exc)
        return None


def _azure_region_keyring() -> str:
    try:
        import keyring
    except ImportError:
        return "eastus"
    try:
        region = keyring.get_password("speedreader", "azure_region")
    except Exception:  # pragma: no cover - defensive
        return "eastus"
    return region or "eastus"