"""Clipboard importer that reads the system clipboard."""

from typing import List, Optional, Protocol

from speedreader.domain import TextSegment
from speedreader.importers.plain_text import PlainTextImporter


class _ClipboardLike(Protocol):
    """Minimal interface expected from a clipboard object."""

    def text(self) -> str: ...


class ClipboardImporter:
    """Read text from the system clipboard and convert it to TextSegments.

    A clipboard-like object can be injected for testing.  If none is provided,
    PySide6's QClipboard is used.
    """

    def __init__(
        self,
        clipboard: Optional[_ClipboardLike] = None,
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

    def _default_clipboard(self) -> _ClipboardLike:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        return app.clipboard()
