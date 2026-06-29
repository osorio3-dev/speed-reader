"""Speedreader: a personal speed-reading station."""

from speedreader.domain import SegmentKind, TextSegment
from speedreader.engine import ReadingEngine
from speedreader.importers.clipboard import ClipboardImporter
from speedreader.importers.markdown import MarkdownImporter
from speedreader.importers.plain_text import PlainTextImporter

__all__ = [
    "SegmentKind",
    "TextSegment",
    "ReadingEngine",
    "MarkdownImporter",
    "PlainTextImporter",
    "ClipboardImporter",
]
