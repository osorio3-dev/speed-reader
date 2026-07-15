"""Voice discovery and selection helpers for Piper, Edge, and Azure."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

QT_VOICE_ID = "qt"
DEFAULT_PIPER_VOICE = "es_MX-ald-x_low"

PREFERRED_VOICES = (
    DEFAULT_PIPER_VOICE,
    "es_MX-claude-high",
    "es_MX-ald-medium",
    "es_AR-daniela-high",
    "es_ES-sharvard-medium",
)

EDGE_VOICE_PREFIX = "edge:"
AZURE_VOICE_PREFIX = "azure:"

EDGE_PREFERRED_VOICES = (
    "es-ES-ElviraNeural",
    "es-ES-XimenaNeural",
    "es-MX-JuanNeural",
    "es-US-AriaNeural",
)

AZURE_VOICES_AVAILABLE = (
    "es-ES-ElviraNeural",
    "es-ES-XimenaNeural",
    "es-MX-JuanNeural",
    "es-MX-DaliaNeural",
    "es-US-AriaNeural",
)

VOICE_LABELS: dict[str, str] = {
    QT_VOICE_ID: "Qt / eSpeak (sistema)",
    DEFAULT_PIPER_VOICE: "Español MX — ligera (~20 MB)",
    "es_MX-claude-high": "Español MX — alta calidad (~60 MB)",
    "es_MX-ald-medium": "Español MX — media (~60 MB)",
    "es_AR-daniela-high": "Español AR — alta (~109 MB)",
    "es_ES-sharvard-medium": "Español ES — media (~73 MB)",
    "es_ES-carlfm-x_low": "Español ES — ligera (~27 MB)",
}

EDGE_VOICE_LABELS: dict[str, str] = {
    f"{EDGE_VOICE_PREFIX}es-ES-ElviraNeural": "Edge · Elvira (ES, online)",
    f"{EDGE_VOICE_PREFIX}es-ES-XimenaNeural": "Edge · Ximena (ES, online)",
    f"{EDGE_VOICE_PREFIX}es-MX-JuanNeural": "Edge · Juan (MX, online)",
    f"{EDGE_VOICE_PREFIX}es-US-AriaNeural": "Edge · Aria (US, online)",
}

AZURE_VOICE_LABELS: dict[str, str] = {
    f"{AZURE_VOICE_PREFIX}es-ES-ElviraNeural": "Azure · Elvira (ES, online)",
    f"{AZURE_VOICE_PREFIX}es-ES-XimenaNeural": "Azure · Ximena (ES, online)",
    f"{AZURE_VOICE_PREFIX}es-MX-JuanNeural": "Azure · Juan (MX, online)",
    f"{AZURE_VOICE_PREFIX}es-MX-DaliaNeural": "Azure · Dalia (MX, online)",
    f"{AZURE_VOICE_PREFIX}es-US-AriaNeural": "Azure · Aria (US, online)",
}


def voice_label(voice_id: str) -> str:
    """Return a human-readable label for a voice id."""
    if voice_id == QT_VOICE_ID:
        return VOICE_LABELS[QT_VOICE_ID]
    if voice_id.startswith(EDGE_VOICE_PREFIX):
        if voice_id in EDGE_VOICE_LABELS:
            return EDGE_VOICE_LABELS[voice_id]
        return f"Edge · {voice_id.removeprefix(EDGE_VOICE_PREFIX)}"
    if voice_id.startswith(AZURE_VOICE_PREFIX):
        if voice_id in AZURE_VOICE_LABELS:
            return AZURE_VOICE_LABELS[voice_id]
        return f"Azure · {voice_id.removeprefix(AZURE_VOICE_PREFIX)}"
    return VOICE_LABELS.get(voice_id, voice_id)


def list_installed_piper_voices(voices_dir: Path) -> list[str]:
    """Return installed Piper voice ids sorted with preferred voices first."""
    installed = {path.stem for path in voices_dir.glob("*.onnx")}
    ordered: list[str] = []
    for voice_id in PREFERRED_VOICES:
        if voice_id in installed:
            ordered.append(voice_id)
    for voice_id in sorted(installed):
        if voice_id not in ordered:
            ordered.append(voice_id)
    return ordered


def list_available_edge_voices() -> list[str]:
    """Return the static list of Edge voice ids surfaced in the UI."""
    return [f"{EDGE_VOICE_PREFIX}{voice}" for voice in EDGE_PREFERRED_VOICES]


def list_available_azure_voices() -> list[str]:
    """Return the static list of Azure voice ids surfaced in the UI."""
    return [f"{AZURE_VOICE_PREFIX}{voice}" for voice in AZURE_VOICES_AVAILABLE]


def resolve_piper_model(
    voices_dir: Path,
    voice_id: Optional[str] = None,
) -> Optional[Path]:
    """Return the ONNX model path for ``voice_id`` or the best available voice."""
    if voice_id and voice_id != QT_VOICE_ID:
        model_path = voices_dir / f"{voice_id}.onnx"
        if model_path.is_file():
            return model_path
        return None

    for preferred in PREFERRED_VOICES:
        model_path = voices_dir / f"{preferred}.onnx"
        if model_path.is_file():
            return model_path

    for model_path in sorted(voices_dir.glob("*.onnx")):
        return model_path
    return None


def resolve_edge_voice(saved_id: Optional[str]) -> Optional[str]:
    """Return the matched Edge voice id (without prefix) or the first default."""
    if saved_id is None:
        return EDGE_PREFERRED_VOICES[0]
    bare = saved_id.removeprefix(EDGE_VOICE_PREFIX)
    if bare in EDGE_PREFERRED_VOICES:
        return bare
    return EDGE_PREFERRED_VOICES[0]


def resolve_azure_voice(saved_id: Optional[str]) -> Optional[str]:
    """Return the matched Azure voice id (without prefix) or the first default."""
    if saved_id is None:
        return AZURE_VOICES_AVAILABLE[0]
    bare = saved_id.removeprefix(AZURE_VOICE_PREFIX)
    if bare in AZURE_VOICES_AVAILABLE:
        return bare
    return AZURE_VOICES_AVAILABLE[0]


def resolve_voice_selection(
    voices_dir: Path,
    saved_voice_id: str,
    installed: Optional[Iterable[str]] = None,
) -> str:
    """Pick the voice id to use from settings and installed models."""
    if saved_voice_id == QT_VOICE_ID:
        return QT_VOICE_ID

    if saved_voice_id.startswith(EDGE_VOICE_PREFIX):
        return saved_voice_id
    if saved_voice_id.startswith(AZURE_VOICE_PREFIX):
        return saved_voice_id

    installed_list = list(installed or list_installed_piper_voices(voices_dir))
    if saved_voice_id in installed_list:
        return saved_voice_id

    for voice_id in PREFERRED_VOICES:
        if voice_id in installed_list:
            return voice_id

    if installed_list:
        return installed_list[0]
    return QT_VOICE_ID