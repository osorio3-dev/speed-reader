"""Tests for JsonSettingsStore — JSON-backed SettingsProtocol implementation."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def test_defaults_when_no_file(tmp_path: Path) -> None:
    """JsonSettingsStore returns defaults when the JSON file does not exist."""
    from speedreader.cli.settings import JsonSettingsStore

    store = JsonSettingsStore(path=tmp_path / "nonexistent.json")
    assert store.load_wpm() == 400
    assert store.load_wpm(default=300) == 300
    assert store.load_tts_wpm() == 400  # falls back to load_wpm()
    assert store.load_tts_wpm(default=250) == 250
    assert store.load_font_size() == 42
    assert store.load_tts_enabled() is False
    assert store.load_reading_profile() == "normal"
    assert store.load_reading_session() is None


def test_save_load_round_trip(tmp_path: Path) -> None:
    """JsonSettingsStore persists values and reloads them correctly."""
    from speedreader.cli.settings import JsonSettingsStore

    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path=path)

    store.save_wpm(500)
    assert store.load_wpm() == 500

    store.save_tts_wpm(300)
    assert store.load_tts_wpm() == 300

    store.save_font_size(48)
    assert store.load_font_size() == 48

    store.save_tts_enabled(True)
    assert store.load_tts_enabled() is True

    store.save_reading_profile("fast")
    assert store.load_reading_profile() == "fast"


def test_persistence_across_instances(tmp_path: Path) -> None:
    """Data written by one instance is readable by a new instance."""
    from speedreader.cli.settings import JsonSettingsStore

    path = tmp_path / "settings.json"

    store1 = JsonSettingsStore(path=path)
    store1.save_wpm(650)
    store1.save_tts_enabled(True)

    store2 = JsonSettingsStore(path=path)
    assert store2.load_wpm() == 650
    assert store2.load_tts_enabled() is True


def test_corrupt_json_uses_defaults(tmp_path: Path) -> None:
    """A corrupt JSON file is silently ignored and defaults are returned."""
    from speedreader.cli.settings import JsonSettingsStore

    path = tmp_path / "settings.json"
    path.write_text("this is not json")

    store = JsonSettingsStore(path=path)
    assert store.load_wpm() == 400
    store.save_wpm(300)  # saves even if initial load was corrupt
    data = json.loads(path.read_text())
    assert data["wpm"] == 300


def test_default_config_path() -> None:
    """JsonSettingsStore uses ~/.config/speedreader/cli-settings.json by default."""
    from speedreader.cli.settings import DEFAULT_CONFIG_PATH, JsonSettingsStore

    store = JsonSettingsStore()
    assert str(store.path).endswith(".config/speedreader/cli-settings.json")
    assert isinstance(store.path, Path)


@pytest.mark.skipif(
    platform.system() == "Windows" and "CI" in os.environ,
    reason="Permission-sensitive on Windows CI",
)
def test_directory_creation(tmp_path: Path) -> None:
    """Parent directories are created automatically when saving."""
    from speedreader.cli.settings import JsonSettingsStore

    nested = tmp_path / "a" / "b" / "c" / "settings.json"
    store = JsonSettingsStore(path=nested)
    store.save_wpm(400)
    assert nested.exists()
    data = json.loads(nested.read_text())
    assert data["wpm"] == 400


def test_empty_json_file_uses_defaults(tmp_path: Path) -> None:
    """An empty JSON object returns all defaults."""
    from speedreader.cli.settings import JsonSettingsStore

    path = tmp_path / "settings.json"
    path.write_text("{}")

    store = JsonSettingsStore(path=path)
    assert store.load_wpm() == 400
    assert store.load_font_size() == 42
    assert store.load_tts_enabled() is False


def test_partial_json_file_mixes_stored_and_defaults(tmp_path: Path) -> None:
    """A JSON file with only some keys returns defaults for missing ones."""
    from speedreader.cli.settings import JsonSettingsStore

    path = tmp_path / "settings.json"
    path.write_text('{"wpm": 250}')

    store = JsonSettingsStore(path=path)
    assert store.load_wpm() == 250        # from file
    assert store.load_font_size() == 42   # default
    assert store.load_tts_enabled() is False  # default

    store.save_tts_enabled(True)
    assert store.load_tts_enabled() is True
    assert store.load_wpm() == 250  # still from file


def test_no_pyside6_imported_on_import() -> None:
    """Importing the settings module does NOT pull in PySide6."""
    code = textwrap.dedent("""\
        import sys
        from speedreader.cli.settings import JsonSettingsStore
        assert "PySide6" not in sys.modules, (
            f"PySide6 IS loaded: {sys.modules.get('PySide6')}"
        )
        print("OK: settings import does not load PySide6")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"PySide6 isolation failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
