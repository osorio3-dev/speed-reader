"""Tests for SettingsProtocol and ClipboardProtocol.

These tests run in a subprocess to get a clean Python process
where the parent conftest hasn't already imported PySide6.
"""

import subprocess
import sys
import textwrap


def test_settings_protocol() -> None:
    """Dict-backed FakeSettings conforms to SettingsProtocol."""
    code = textwrap.dedent("""\
        from __future__ import annotations

        from speedreader.core.protocols import SettingsProtocol, ClipboardProtocol


        class FakeSettings:
            \"\"\"Dict-backed settings that conforms to SettingsProtocol.\"\"\"

            def __init__(self) -> None:
                self._store: dict[str, object] = {}

            def load_wpm(self, default: int = 400) -> int:
                return int(self._store.get("wpm", default))  # type: ignore[return-value]

            def save_wpm(self, wpm: int) -> None:
                self._store["wpm"] = wpm

            def load_tts_wpm(self, default: int | None = None) -> int:
                fallback = default if default is not None else self.load_wpm()
                return int(self._store.get("tts_wpm", fallback))  # type: ignore[return-value]

            def save_tts_wpm(self, wpm: int) -> None:
                self._store["tts_wpm"] = wpm

            def load_font_size(self, default: int = 42) -> int:
                return int(self._store.get("font_size", default))  # type: ignore[return-value]

            def save_font_size(self, size: int) -> None:
                self._store["font_size"] = size

            def load_tts_enabled(self, default: bool = False) -> bool:
                value = self._store.get("tts_enabled", default)
                if isinstance(value, str):
                    return value.lower() in {"1", "true", "yes"}
                return bool(value)

            def save_tts_enabled(self, enabled: bool) -> None:
                self._store["tts_enabled"] = enabled

            def load_reading_profile(self, default: str = "normal") -> str:
                return str(self._store.get("reading_profile", default))

            def save_reading_profile(self, profile_id: str) -> None:
                self._store["reading_profile"] = profile_id

            def load_reading_session(self) -> object:
                return None

            def save_reading_session(self, source_path: str, position: int) -> None:
                pass

            def clear_reading_session(self) -> None:
                pass


        # Verify FakeSettings satisfies SettingsProtocol (structural subtyping)
        settings: SettingsProtocol = FakeSettings()

        # Test defaults
        assert settings.load_wpm() == 400
        assert settings.load_wpm(default=300) == 300
        assert settings.load_tts_wpm() == 400  # falls back to load_wpm()
        assert settings.load_tts_wpm(default=250) == 250
        assert settings.load_font_size() == 42
        assert settings.load_font_size(default=36) == 36
        assert settings.load_tts_enabled() is False
        assert settings.load_tts_enabled(default=True) is True
        assert settings.load_reading_profile() == "normal"
        assert settings.load_reading_profile(default="fast") == "fast"
        assert settings.load_reading_session() is None

        # Test save/load round-trips
        settings.save_wpm(500)
        assert settings.load_wpm() == 500

        settings.save_tts_wpm(300)
        assert settings.load_tts_wpm() == 300

        settings.save_font_size(48)
        assert settings.load_font_size() == 48

        settings.save_tts_enabled(True)
        assert settings.load_tts_enabled() is True

        settings.save_reading_profile("fast")
        assert settings.load_reading_profile() == "fast"

        # Test ClipboardProtocol
        class FakeClipboard:
            def __init__(self, text: str = "") -> None:
                self._text = text
            def text(self) -> str:
                return self._text

        cb: ClipboardProtocol = FakeClipboard("hello")
        assert cb.text() == "hello"

        cb_empty: ClipboardProtocol = FakeClipboard("")
        assert cb_empty.text() == ""

        print("OK: SettingsProtocol and ClipboardProtocol work as expected")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"SettingsProtocol test failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
