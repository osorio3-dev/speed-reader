"""Create the best available offline speech backend."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from speedreader.speech.base import SpeechBackend
from speedreader.speech.qt_backend import QtSpeechBackend
from speedreader.speech.voices import QT_VOICE_ID, resolve_piper_model

TtsBackendPreference = Literal["auto", "piper", "qt"]
DEFAULT_VOICES_DIR = Path.home() / ".local" / "share" / "speedreader" / "voices"


def create_speech_backend(
    preference: TtsBackendPreference = "auto",
    voices_dir: Optional[Path] = None,
    voice_id: Optional[str] = None,
) -> SpeechBackend:
    """Return Piper when available, otherwise QTextToSpeech."""
    voices_path = voices_dir or DEFAULT_VOICES_DIR
    if voice_id == QT_VOICE_ID:
        return QtSpeechBackend()

    if preference != "qt":
        piper_backend = _try_create_piper_backend(voices_path, voice_id)
        if piper_backend is not None:
            return piper_backend
    return QtSpeechBackend()


def _try_create_piper_backend(
    voices_dir: Path,
    voice_id: Optional[str] = None,
) -> Optional[SpeechBackend]:
    try:
        from speedreader.speech.piper_backend import PiperSpeechBackend
    except ImportError:
        return None

    model_path = resolve_piper_model(voices_dir, voice_id)
    if model_path is None:
        return None

    try:
        return PiperSpeechBackend(model_path)
    except Exception:
        return None
