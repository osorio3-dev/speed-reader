"""Persistent user preferences."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings

from speedreader.core.protocols import SettingsProtocol
from speedreader.engine import DEFAULT_WPM
from speedreader.profiles import DEFAULT_PROFILE_ID, normalize_profile_id, profile_label
from speedreader.speech.voices import DEFAULT_PIPER_VOICE, QT_VOICE_ID

# SettingsStore structurally conforms to SettingsProtocol via duck-typing.
# All required load/save methods are defined below with matching signatures.

MIN_WPM = 100
MAX_WPM = 1500
WPM_STEP = 25
DEFAULT_FONT_SIZE = 42
MIN_FONT_SIZE = 24
MAX_FONT_SIZE = 96
_WPM_KEY = "wpm"
_TTS_WPM_KEY = "tts/wpm"
_FONT_SIZE_KEY = "font_size"
_SESSION_SOURCE_KIND_KEY = "session/source_kind"
_SESSION_SOURCE_PATH_KEY = "session/source_path"
_SESSION_POSITION_KEY = "session/position"
_FILE_SOURCE_KIND = "file"
_TTS_ENABLED_KEY = "tts/enabled"
_TTS_BACKEND_KEY = "tts/backend"
_TTS_VOICES_DIR_KEY = "tts/voices_dir"
_TTS_VOICE_KEY = "tts/voice"
_READING_PROFILE_KEY = "reading/profile"
DEFAULT_VOICES_DIR = Path.home() / ".local" / "share" / "speedreader" / "voices"


@dataclass(frozen=True)
class ReadingSession:
    """A resumable file reading session."""

    source_path: str
    position: int


def clamp_wpm(value: object, fallback: int = DEFAULT_WPM) -> int:
    """Clamp ``value`` to the supported WPM range."""
    try:
        wpm = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return snap_wpm(fallback, fallback)
    return snap_wpm(wpm, fallback)


def snap_wpm(value: int, fallback: int = DEFAULT_WPM) -> int:
    """Clamp and round ``value`` to the configured WPM step."""
    try:
        wpm = int(value)
    except (TypeError, ValueError):
        wpm = fallback
    bounded = max(MIN_WPM, min(MAX_WPM, wpm))
    return int(round(bounded / WPM_STEP) * WPM_STEP)


def clamp_font_size(value: object, fallback: int = DEFAULT_FONT_SIZE) -> int:
    """Clamp ``value`` to the supported font size range."""
    try:
        size = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback
    return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))


class SettingsStore:
    """Load and save speedreader preferences."""

    def __init__(self, settings: Optional[QSettings] = None) -> None:
        self._settings = settings or QSettings("speedreader", "speedreader")

    def load_wpm(self, default: int = DEFAULT_WPM) -> int:
        """Return the saved WPM or ``default``."""
        return clamp_wpm(self._settings.value(_WPM_KEY, default), default)

    def save_wpm(self, wpm: int) -> None:
        """Persist the current WPM."""
        self._settings.setValue(_WPM_KEY, clamp_wpm(wpm))

    def load_tts_wpm(self, default: Optional[int] = None) -> int:
        """Return the saved TTS WPM or ``default``."""
        fallback = self.load_wpm() if default is None else default
        return clamp_wpm(self._settings.value(_TTS_WPM_KEY, fallback), fallback)

    def save_tts_wpm(self, wpm: int) -> None:
        """Persist the TTS speaking WPM."""
        self._settings.setValue(_TTS_WPM_KEY, clamp_wpm(wpm))

    def load_font_size(self, default: int = DEFAULT_FONT_SIZE) -> int:
        """Return the saved RSVP font size or ``default``."""
        return clamp_font_size(self._settings.value(_FONT_SIZE_KEY, default), default)

    def save_font_size(self, size: int) -> None:
        """Persist the RSVP font size."""
        self._settings.setValue(_FONT_SIZE_KEY, clamp_font_size(size))

    def load_tts_enabled(self, default: bool = False) -> bool:
        """Return whether TTS-driven reading is enabled."""
        value = self._settings.value(_TTS_ENABLED_KEY, default)
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes"}
        return bool(value)

    def save_tts_enabled(self, enabled: bool) -> None:
        """Persist the TTS enabled flag."""
        self._settings.setValue(_TTS_ENABLED_KEY, enabled)

    def load_tts_backend(self, default: str = "auto") -> str:
        """Return preferred TTS backend: auto, piper, or qt."""
        value = str(self._settings.value(_TTS_BACKEND_KEY, default))
        if value in {"auto", "piper", "qt"}:
            return value
        return default

    def save_tts_backend(self, backend: str) -> None:
        """Persist the preferred TTS backend."""
        if backend not in {"auto", "piper", "qt"}:
            backend = "auto"
        self._settings.setValue(_TTS_BACKEND_KEY, backend)

    def load_voices_dir(self) -> Path:
        """Return the directory containing Piper voice models."""
        value = self._settings.value(_TTS_VOICES_DIR_KEY, str(DEFAULT_VOICES_DIR))
        return Path(str(value))

    def save_voices_dir(self, voices_dir: Path) -> None:
        """Persist the Piper voices directory."""
        self._settings.setValue(_TTS_VOICES_DIR_KEY, str(voices_dir))

    def load_tts_voice(self, default: str = DEFAULT_PIPER_VOICE) -> str:
        """Return the selected TTS voice id (Piper name or ``qt``)."""
        value = str(self._settings.value(_TTS_VOICE_KEY, default))
        if value == QT_VOICE_ID:
            return QT_VOICE_ID
        return value

    def save_tts_voice(self, voice_id: str) -> None:
        """Persist the selected TTS voice id."""
        self._settings.setValue(_TTS_VOICE_KEY, voice_id)

    def load_reading_profile(self, default: str = DEFAULT_PROFILE_ID) -> str:
        """Return the saved reading profile id."""
        return normalize_profile_id(str(self._settings.value(_READING_PROFILE_KEY, default)))

    def save_reading_profile(self, profile_id: str) -> None:
        """Persist the reading profile id."""
        self._settings.setValue(_READING_PROFILE_KEY, normalize_profile_id(profile_id))

    def load_reading_profile_label(self) -> str:
        """Return the display label for the saved reading profile."""
        return profile_label(self.load_reading_profile())

    def load_reading_session(self) -> Optional[ReadingSession]:
        """Return the last saved file session if it is still valid."""
        if self._settings.value(_SESSION_SOURCE_KIND_KEY, "") != _FILE_SOURCE_KIND:
            return None

        source_path = self._settings.value(_SESSION_SOURCE_PATH_KEY, "")
        if not source_path or not Path(source_path).is_file():
            return None

        try:
            position = int(self._settings.value(_SESSION_POSITION_KEY, 0))
        except (TypeError, ValueError):
            position = 0

        return ReadingSession(source_path=source_path, position=max(position, 0))

    def save_reading_session(self, source_path: str, position: int) -> None:
        """Persist a resumable file reading session."""
        self._settings.setValue(_SESSION_SOURCE_KIND_KEY, _FILE_SOURCE_KIND)
        self._settings.setValue(_SESSION_SOURCE_PATH_KEY, source_path)
        self._settings.setValue(_SESSION_POSITION_KEY, max(position, 0))

    def clear_reading_session(self) -> None:
        """Remove any saved reading session."""
        self._settings.remove(_SESSION_SOURCE_KIND_KEY)
        self._settings.remove(_SESSION_SOURCE_PATH_KEY)
        self._settings.remove(_SESSION_POSITION_KEY)
