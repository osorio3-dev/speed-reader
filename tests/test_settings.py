"""Tests for persistent user settings."""

from PySide6.QtCore import QSettings

from speedreader.settings import SettingsStore, clamp_wpm


def test_clamp_wpm_limits_range() -> None:
    assert clamp_wpm(400) == 400
    assert clamp_wpm(50) == 100
    assert clamp_wpm(2000) == 1000
    assert clamp_wpm("invalid", 400) == 400


def test_settings_store_roundtrips_wpm(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_wpm(450)
    assert store.load_wpm() == 450

    store.save_wpm(9999)
    assert store.load_wpm() == 1000
