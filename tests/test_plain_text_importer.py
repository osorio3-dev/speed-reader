"""Tests for the plain text importer."""

from speedreader import PlainTextImporter, SegmentKind


def test_single_paragraph() -> None:
    importer = PlainTextImporter()
    segments = importer.parse("This is a single paragraph.")
    assert len(segments) == 1
    assert segments[0].kind == SegmentKind.PARAGRAPH
    assert segments[0].content == "This is a single paragraph."


def test_multiple_paragraphs() -> None:
    source = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    importer = PlainTextImporter()
    segments = importer.parse(source)
    assert len(segments) == 3
    assert all(s.kind == SegmentKind.PARAGRAPH for s in segments)
    assert segments[0].content == "First paragraph."
    assert segments[1].content == "Second paragraph."
    assert segments[2].content == "Third paragraph."


def test_empty_and_whitespace_only_input() -> None:
    importer = PlainTextImporter()
    assert importer.parse("") == []
    assert importer.parse("   \n\n  \n") == []
