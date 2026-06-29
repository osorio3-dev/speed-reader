"""Tests for the file importer."""

from pathlib import Path

from speedreader import FileImporter, SegmentKind
from speedreader.importers.file import is_supported_file


def test_read_txt_file(tmp_path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")

    segments = FileImporter().read(file_path)

    assert len(segments) == 2
    assert all(segment.kind == SegmentKind.PARAGRAPH for segment in segments)
    assert segments[0].content == "First paragraph."
    assert segments[1].content == "Second paragraph."


def test_read_markdown_file(tmp_path) -> None:
    file_path = tmp_path / "notes.md"
    file_path.write_text("# Title\n\nBody text.", encoding="utf-8")

    segments = FileImporter().read(file_path)

    assert len(segments) == 2
    assert segments[0].kind == SegmentKind.HEADING
    assert segments[0].content == "Title"
    assert segments[1].content == "Body text."


def test_is_supported_file() -> None:
    assert is_supported_file("article.md")
    assert is_supported_file("notes.txt")
    assert not is_supported_file("image.png")
