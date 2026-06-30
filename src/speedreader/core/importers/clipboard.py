"""Clipboard importer that reads the system clipboard — zero Qt imports."""

from typing import List, Optional

from speedreader.core.domain import TextSegment
from speedreader.core.importers.plain_text import PlainTextImporter
from speedreader.core.protocols import ClipboardProtocol


class ClipboardImporter:
    """Read text from the system clipboard and convert it to TextSegments.

    A clipboard-like object can be injected for testing.  If none is provided,
    PySide6's QClipboard is used.
    """

    def __init__(
        self,
        clipboard: Optional[ClipboardProtocol] = None,
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
        clipboard = self._clipboard or self._default_clipboard()
        return clipboard.text()

    def _default_clipboard(self) -> ClipboardProtocol:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        return app.clipboard()
