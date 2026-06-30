"""Markdown importer that produces clean TextSegments — zero Qt imports."""

from typing import Iterable, List

from mistletoe import Document
from mistletoe.block_token import (
    BlockCode,
    CodeFence,
    Heading,
    HtmlBlock,
    List as MdList,
    ListItem,
    Paragraph,
    Quote,
    SetextHeading,
    Table,
    TableRow,
    ThematicBreak,
)
from mistletoe.span_token import Emphasis, LineBreak, Link, RawText, Strong

from speedreader.core.domain import SegmentKind, TextSegment


def _iter_children(token) -> Iterable:
    """Return block or span children, treating missing children as empty."""
    children = getattr(token, "children", None)
    return children or []


class MarkdownImporter:
    """Parse Markdown into a list of TextSegments.

    The default behaviour strips Markdown syntax so that reading engines do not
    speak characters such as ``#``, ``*`` or back-ticks.  Structure (headings,
    lists, code blocks, blockquotes) is preserved as segment metadata.
    """

    def parse(self, source: str) -> List[TextSegment]:
        """Return TextSegments for the given Markdown source."""
        document = Document(source)
        segments: List[TextSegment] = []
        for child in document.children:
            self._parse_block(child, segments)
        return segments

    def _parse_block(self, token, segments: List[TextSegment]) -> None:
        if isinstance(token, (Heading, SetextHeading)):
            text = _inline_text(token).strip()
            segments.append(
                TextSegment(content=text, kind=SegmentKind.HEADING, level=token.level)
            )

        elif isinstance(token, Paragraph):
            text = _inline_text(token).strip()
            if text:
                segments.append(TextSegment(content=text, kind=SegmentKind.PARAGRAPH))

        elif isinstance(token, MdList):
            for item in _iter_children(token):
                self._parse_block(item, segments)

        elif isinstance(token, ListItem):
            text = _block_text(_iter_children(token)).strip()
            if text:
                segments.append(TextSegment(content=text, kind=SegmentKind.LIST_ITEM))

        elif isinstance(token, (CodeFence, BlockCode)):
            language = getattr(token, "language", None)
            segments.append(
                TextSegment(
                    content=token.content,
                    kind=SegmentKind.CODE_BLOCK,
                    language=language,
                )
            )

        elif isinstance(token, Quote):
            text = _quote_text(token)
            cleaned = "\n".join(
                line.lstrip(">").lstrip() for line in text.splitlines()
            ).strip()
            if cleaned:
                segments.append(
                    TextSegment(content=cleaned, kind=SegmentKind.BLOCKQUOTE)
                )

        elif isinstance(token, Table):
            header = getattr(token, "header", None)
            if header is not None:
                self._parse_table_row(header, segments)
            for row in _iter_children(token):
                self._parse_table_row(row, segments)

        elif isinstance(token, HtmlBlock):
            text = getattr(token, "content", _inline_text(token)).strip()
            if text:
                segments.append(TextSegment(content=text, kind=SegmentKind.PARAGRAPH))

        elif isinstance(token, ThematicBreak):
            return

        elif _iter_children(token):
            for child in _iter_children(token):
                self._parse_block(child, segments)

    def _parse_table_row(self, row: TableRow, segments: List[TextSegment]) -> None:
        cells = [_inline_text(cell).strip() for cell in _iter_children(row)]
        text = " | ".join(cell for cell in cells if cell)
        if text:
            segments.append(TextSegment(content=text, kind=SegmentKind.PARAGRAPH))


def _inline_text(token, line_break: str = " ") -> str:
    """Extract plain text from an inline token tree."""
    if isinstance(token, RawText):
        return token.content

    if isinstance(token, (Strong, Emphasis)):
        return "".join(_inline_text(child, line_break) for child in _iter_children(token))

    if isinstance(token, Link):
        # For the MVP we read the visible link text only, not the URL.
        return "".join(_inline_text(child, line_break) for child in _iter_children(token))

    if isinstance(token, LineBreak):
        return line_break

    if _iter_children(token):
        return "".join(_inline_text(child, line_break) for child in _iter_children(token))

    return ""


def _block_text(tokens) -> str:
    """Extract plain text from a sequence of block tokens."""
    parts: List[str] = []
    for token in tokens:
        if isinstance(token, (Heading, Paragraph)):
            parts.append(_inline_text(token))
        elif isinstance(token, (CodeFence, BlockCode)):
            parts.append(token.content)
        elif isinstance(token, Quote):
            parts.append(_quote_text(token))
        elif _iter_children(token):
            parts.append(_block_text(_iter_children(token)))
    return " ".join(part for part in parts if part)


def _quote_text(token) -> str:
    """Extract plain text from a quote, preserving line breaks."""
    parts: List[str] = []
    for child in _iter_children(token):
        if isinstance(child, (Heading, Paragraph, SetextHeading)):
            parts.append(_inline_text(child, line_break="\n").strip())
        elif isinstance(child, (CodeFence, BlockCode)):
            parts.append(child.content)
        elif isinstance(child, Quote):
            parts.append(_quote_text(child))
        elif _iter_children(child):
            parts.append(_quote_text(child))
    return "\n".join(part for part in parts if part)
