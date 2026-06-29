"""Tests for speech helpers and backend selection."""

from pathlib import Path

from speedreader.speech.factory import create_speech_backend
from speedreader.speech.rate import wpm_to_length_scale, wpm_to_qt_rate
from speedreader.speech.piper_backend import find_voice_model
from speedreader.speech.voices import (
    DEFAULT_PIPER_VOICE,
    QT_VOICE_ID,
    list_installed_piper_voices,
    resolve_voice_selection,
)


def test_wpm_to_qt_rate_maps_around_zero_at_base() -> None:
    assert wpm_to_qt_rate(300) == 0.0
    assert wpm_to_qt_rate(900) == 1.0
    assert wpm_to_qt_rate(100) < 0


def test_wpm_to_length_scale_inverts_wpm() -> None:
    assert wpm_to_length_scale(300) == 1.0
    assert wpm_to_length_scale(600) == 0.5
    assert wpm_to_length_scale(1500) == 0.2


def test_wpm_to_length_scale_has_minimum_for_extreme_wpm() -> None:
    from speedreader.speech.rate import MIN_PIPER_LENGTH_SCALE

    assert wpm_to_length_scale(3000) == MIN_PIPER_LENGTH_SCALE


def test_wpm_to_length_scale_applies_pace_multiplier() -> None:
    assert wpm_to_length_scale(300, pace_multiplier=1.5) > wpm_to_length_scale(300)


def test_find_voice_model_prefers_light_latin_voice(tmp_path: Path) -> None:
    voices_dir = tmp_path / "voices"
    voices_dir.mkdir()
    (voices_dir / "es_ES-sharvard-medium.onnx").write_text("x", encoding="utf-8")
    light = voices_dir / "es_MX-ald-x_low.onnx"
    light.write_text("x", encoding="utf-8")
    heavy = voices_dir / "es_MX-claude-high.onnx"
    heavy.write_text("x", encoding="utf-8")

    assert find_voice_model(voices_dir) == light


def test_find_voice_model_honors_explicit_voice_id(tmp_path: Path) -> None:
    voices_dir = tmp_path / "voices"
    voices_dir.mkdir()
    light = voices_dir / "es_MX-ald-x_low.onnx"
    light.write_text("x", encoding="utf-8")
    heavy = voices_dir / "es_MX-claude-high.onnx"
    heavy.write_text("x", encoding="utf-8")

    assert find_voice_model(voices_dir, "es_MX-claude-high") == heavy


def test_list_installed_piper_voices_orders_preferred_first(tmp_path: Path) -> None:
    voices_dir = tmp_path / "voices"
    voices_dir.mkdir()
    (voices_dir / "zz_custom-low.onnx").write_text("x", encoding="utf-8")
    (voices_dir / "es_MX-claude-high.onnx").write_text("x", encoding="utf-8")
    (voices_dir / f"{DEFAULT_PIPER_VOICE}.onnx").write_text("x", encoding="utf-8")

    assert list_installed_piper_voices(voices_dir) == [
        DEFAULT_PIPER_VOICE,
        "es_MX-claude-high",
        "zz_custom-low",
    ]


def test_resolve_voice_selection_falls_back_to_qt_when_empty(tmp_path: Path) -> None:
    voices_dir = tmp_path / "voices"
    voices_dir.mkdir()

    assert resolve_voice_selection(voices_dir, DEFAULT_PIPER_VOICE) == QT_VOICE_ID


def test_create_speech_backend_falls_back_to_qt() -> None:
    backend = create_speech_backend(preference="qt", voices_dir=Path("/no-such-dir"))
    assert backend.name == "Qt"
