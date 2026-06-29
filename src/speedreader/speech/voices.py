"""Piper voice discovery and selection helpers."""

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

VOICE_LABELS: dict[str, str] = {
    QT_VOICE_ID: "Qt / eSpeak (sistema)",
    DEFAULT_PIPER_VOICE: "Español MX — ligera (~20 MB)",
    "es_MX-claude-high": "Español MX — alta calidad (~60 MB)",
    "es_MX-ald-medium": "Español MX — media (~60 MB)",
    "es_AR-daniela-high": "Español AR — alta (~109 MB)",
    "es_ES-sharvard-medium": "Español ES — media (~73 MB)",
    "es_ES-carlfm-x_low": "Español ES — ligera (~27 MB)",
}


def voice_label(voice_id: str) -> str:
    """Return a human-readable label for a voice id."""
    if voice_id == QT_VOICE_ID:
        return VOICE_LABELS[QT_VOICE_ID]
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


def resolve_voice_selection(
    voices_dir: Path,
    saved_voice_id: str,
    installed: Optional[Iterable[str]] = None,
) -> str:
    """Pick the voice id to use from settings and installed models."""
    if saved_voice_id == QT_VOICE_ID:
        return QT_VOICE_ID

    installed_list = list(installed or list_installed_piper_voices(voices_dir))
    if saved_voice_id in installed_list:
        return saved_voice_id

    for voice_id in PREFERRED_VOICES:
        if voice_id in installed_list:
            return voice_id

    if installed_list:
        return installed_list[0]
    return QT_VOICE_ID
