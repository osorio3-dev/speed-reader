"""Plain text importer that splits raw text into segments."""

from typing import List

from speedreader.domain import SegmentKind, TextSegment


class PlainTextImporter:
    """Convert plain text into a list of TextSegments.

    Blank lines separate paragraphs.  Leading and trailing whitespace is
    stripped from each segment.
    """

    def parse(self, source: str) -> List[TextSegment]:
        """Return TextSegments for the given plain text source."""
        parts = [part.strip() for part in source.split("\n\n") if part.strip()]
        return [
            TextSegment(content=part, kind=SegmentKind.PARAGRAPH) for part in parts
        ]
