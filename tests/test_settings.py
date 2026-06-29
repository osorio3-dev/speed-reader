"""Tests for persistent user settings."""

from PySide6.QtCore import QSettings

from speedreader.settings import SettingsStore, clamp_font_size, clamp_wpm


def test_clamp_wpm_limits_range() -> None:
    assert clamp_wpm(400) == 400
    assert clamp_wpm(50) == 100
    assert clamp_wpm(2000) == 1500
    assert clamp_wpm("invalid", 400) == 400


def test_snap_wpm_rounds_to_step() -> None:
    from speedreader.settings import snap_wpm

    assert snap_wpm(412) == 400
    assert snap_wpm(413) == 425
    assert snap_wpm(1512) == 1500


def test_clamp_font_size_limits_range() -> None:
    assert clamp_font_size(42) == 42
    assert clamp_font_size(10) == 24
    assert clamp_font_size(120) == 96
    assert clamp_font_size("invalid", 42) == 42


def test_settings_store_roundtrips_font_size(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_font_size(52)
    assert store.load_font_size() == 52

    store.save_font_size(10)
    assert store.load_font_size() == 24


def test_settings_store_roundtrips_wpm(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_wpm(450)
    assert store.load_wpm() == 450

    store.save_wpm(9999)
    assert store.load_wpm() == 1500


def test_settings_store_roundtrips_reading_session(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)
    file_path = tmp_path / "chapter.md"
    file_path.write_text("# Title\n\nBody", encoding="utf-8")

    store.save_reading_session(str(file_path), 12)
    session = store.load_reading_session()

    assert session is not None
    assert session.source_path == str(file_path)
    assert session.position == 12


def test_load_reading_session_returns_none_for_missing_file(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_reading_session(str(tmp_path / "missing.md"), 4)
    assert store.load_reading_session() is None


def test_clear_reading_session(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello", encoding="utf-8")

    store.save_reading_session(str(file_path), 1)
    store.clear_reading_session()
    assert store.load_reading_session() is None


def test_settings_store_roundtrips_tts_voice(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_tts_voice("es_MX-claude-high")
    assert store.load_tts_voice() == "es_MX-claude-high"

    store.save_tts_voice("qt")
    assert store.load_tts_voice() == "qt"


def test_settings_store_roundtrips_tts_wpm(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_tts_wpm(625)
    assert store.load_tts_wpm() == 625

    store.save_tts_wpm(1512)
    assert store.load_tts_wpm() == 1500


def test_settings_store_roundtrips_reading_profile(tmp_path) -> None:
    ini_path = tmp_path / "speedreader.ini"
    settings = QSettings(str(ini_path), QSettings.Format.IniFormat)
    store = SettingsStore(settings)

    store.save_reading_profile("study")
    assert store.load_reading_profile() == "study"
    assert store.load_reading_profile_label() == "Estudio"
