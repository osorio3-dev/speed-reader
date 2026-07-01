"""Clipboard importer that reads the system clipboard — zero Qt imports."""

from typing import List, Optional

from speedreader.core.domain import TextSegment
from speedreader.core.importers.plain_text import PlainTextImporter
from speedreader.core.protocols import ClipboardProtocol


class ClipboardImporter:
    """Read text from an injected clipboard and convert it to TextSegments."""

    def __init__(
        self,
        clipboard: ClipboardProtocol,
        text_importer: Optional[PlainTextImporter] = None,
    ) -> None:
        self._clipboard = clipboard
        self._text_importer = text_importer or PlainTextImporter()

    def read(self) -> List[TextSegment]:
        """Return TextSegments from the current clipboard text."""
        text = self.read_text()
        if not text:
            return []
        return self._text_importer.parse(text)

    def read_text(self) -> str:
        """Return the raw clipboard text."""
        return self._clipboard.text()
