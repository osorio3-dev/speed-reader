"""Tests for ORP display helpers."""

from speedreader.orp import format_word_with_orp, optimal_recognition_index


def test_orp_index_scales_with_word_length() -> None:
    assert optimal_recognition_index("I") == 0
    assert optimal_recognition_index("the") == 1
    assert optimal_recognition_index("reading") == 2
    assert optimal_recognition_index("speedreader") == 3
    assert optimal_recognition_index("extraordinarily") == 4


def test_orp_ignores_trailing_punctuation() -> None:
    assert optimal_recognition_index("hello,") == 1
    assert optimal_recognition_index('"stop!"') == 2


def test_format_word_with_orp_highlights_expected_letter() -> None:
    html = format_word_with_orp("reading")
    assert html.startswith("re")
    assert '">a</span>' in html
    assert html.endswith("ding")
