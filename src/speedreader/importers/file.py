"""File importer that reads text files from disk."""

from pathlib import Path
from typing import List, Union

from speedreader.domain import TextSegment
from speedreader.importers.markdown import MarkdownImporter
from speedreader.importers.plain_text import PlainTextImporter

_MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown", ".mkd"}
_TEXT_SUFFIXES = {".txt", ""}
SUPPORTED_SUFFIXES = _MARKDOWN_SUFFIXES | _TEXT_SUFFIXES


def is_supported_file(path: Union[str, Path]) -> bool:
    """Return whether ``path`` has a supported text extension."""
    return Path(path).suffix.lower() in SUPPORTED_SUFFIXES


class FileImporter:
    """Read ``.txt`` or markdown files into TextSegments."""

    def __init__(
        self,
        markdown_importer: MarkdownImporter | None = None,
        plain_text_importer: PlainTextImporter | None = None,
    ) -> None:
        self._markdown_importer = markdown_importer or MarkdownImporter()
        self._plain_text_importer = plain_text_importer or PlainTextImporter()

    def read(self, path: Union[str, Path]) -> List[TextSegment]:
        """Return TextSegments parsed from the file at ``path``."""
        file_path = Path(path)
        source = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() in _MARKDOWN_SUFFIXES:
            return self._markdown_importer.parse(source)
        return self._plain_text_importer.parse(source)
