"""JSON-backed SettingsProtocol implementation — zero Qt imports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

DEFAULT_CONFIG_DIR = Path(user_config_dir("speedreader"))
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "cli-settings.json"


class JsonSettingsStore:
    """SettingsProtocol implementation backed by a JSON file.

    Persists reading preferences to ``~/.config/speedreader/cli-settings.json``
    by default.  An alternate path can be injected for testing.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
        self._data: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Read JSON from disk, falling back to empty dict on any error."""
        try:
            if self._path.exists():
                raw = self._path.read_text(encoding="utf-8")
                self._data = json.loads(raw)
            else:
                self._data = {}
        except (json.JSONDecodeError, OSError):
            self._data = {}

    def _save(self) -> None:
        """Write current data to the JSON file, creating directories."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            # Silently ignore write errors to match SettingsProtocol contract
            pass

    # ------------------------------------------------------------------
    # SettingsProtocol — WPM
    # ------------------------------------------------------------------

    def load_wpm(self, default: int = 400) -> int:
        return int(self._data.get("wpm", default))

    def save_wpm(self, wpm: int) -> None:
        self._data["wpm"] = wpm
        self._save()

    # ------------------------------------------------------------------
    # SettingsProtocol — TTS WPM
    # ------------------------------------------------------------------

    def load_tts_wpm(self, default: int | None = None) -> int:
        fallback = default if default is not None else self.load_wpm()
        return int(self._data.get("tts_wpm", fallback))

    def save_tts_wpm(self, wpm: int) -> None:
        self._data["tts_wpm"] = wpm
        self._save()

    # ------------------------------------------------------------------
    # SettingsProtocol — font size
    # ------------------------------------------------------------------

    def load_font_size(self, default: int = 42) -> int:
        return int(self._data.get("font_size", default))

    def save_font_size(self, size: int) -> None:
        self._data["font_size"] = size
        self._save()

    # ------------------------------------------------------------------
    # SettingsProtocol — TTS enabled
    # ------------------------------------------------------------------

    def load_tts_enabled(self, default: bool = False) -> bool:
        value = self._data.get("tts_enabled", default)
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes"}
        return bool(value)

    def save_tts_enabled(self, enabled: bool) -> None:
        self._data["tts_enabled"] = enabled
        self._save()

    # ------------------------------------------------------------------
    # SettingsProtocol — reading profile
    # ------------------------------------------------------------------

    def load_reading_profile(self, default: str = "normal") -> str:
        return str(self._data.get("reading_profile", default))

    def save_reading_profile(self, profile_id: str) -> None:
        self._data["reading_profile"] = profile_id
        self._save()

    # ------------------------------------------------------------------
    # SettingsProtocol — reading session (not used by CLI)
    # ------------------------------------------------------------------

    def load_reading_session(self) -> object:
        return None

    def save_reading_session(self, source_path: str, position: int) -> None:
        pass

    def clear_reading_session(self) -> None:
        pass
