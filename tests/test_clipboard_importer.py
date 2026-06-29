"""Tests for the clipboard importer."""

from speedreader import ClipboardImporter, SegmentKind


class FakeClipboard:
    def __init__(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


def test_clipboard_with_text() -> None:
    clipboard = FakeClipboard("First paragraph.\n\nSecond paragraph.")
    importer = ClipboardImporter(clipboard=clipboard)
    segments = importer.read()
    assert len(segments) == 2
    assert all(s.kind == SegmentKind.PARAGRAPH for s in segments)
    assert segments[0].content == "First paragraph."
    assert segments[1].content == "Second paragraph."


def test_empty_clipboard() -> None:
    clipboard = FakeClipboard("")
    importer = ClipboardImporter(clipboard=clipboard)
    assert importer.read() == []
