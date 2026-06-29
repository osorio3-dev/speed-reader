"""Markdown importer that produces clean TextSegments."""

from typing import List

from mistletoe import Document
from mistletoe.block_token import BlockCode, CodeFence, Heading, List, ListItem, Paragraph, Quote
from mistletoe.span_token import Emphasis, LineBreak, Link, RawText, Strong

from speedreader.domain import SegmentKind, TextSegment


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
        if isinstance(token, Heading):
            text = _inline_text(token).strip()
            segments.append(
                TextSegment(content=text, kind=SegmentKind.HEADING, level=token.level)
            )

        elif isinstance(token, Paragraph):
            text = _inline_text(token).strip()
            if text:
                segments.append(TextSegment(content=text, kind=SegmentKind.PARAGRAPH))

        elif isinstance(token, List):
            for item in token.children:
                self._parse_block(item, segments)

        elif isinstance(token, ListItem):
            text = _block_text(token.children).strip()
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

        elif hasattr(token, "children"):
            for child in token.children:
                self._parse_block(child, segments)


def _inline_text(token, line_break: str = " ") -> str:
    """Extract plain text from an inline token tree."""
    if isinstance(token, RawText):
        return token.content

    if isinstance(token, (Strong, Emphasis)):
        return "".join(_inline_text(child, line_break) for child in token.children)

    if isinstance(token, Link):
        # For the MVP we read the visible link text only, not the URL.
        return "".join(_inline_text(child, line_break) for child in token.children)

    if isinstance(token, LineBreak):
        return line_break

    if hasattr(token, "children"):
        return "".join(_inline_text(child, line_break) for child in token.children)

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
        elif hasattr(token, "children"):
            parts.append(_block_text(token.children))
    return " ".join(part for part in parts if part)


def _quote_text(token) -> str:
    """Extract plain text from a quote, preserving line breaks."""
    parts: List[str] = []
    for child in token.children:
        if isinstance(child, (Heading, Paragraph)):
            parts.append(_inline_text(child, line_break="\n").strip())
        elif isinstance(child, (CodeFence, BlockCode)):
            parts.append(child.content)
        elif isinstance(child, Quote):
            parts.append(_quote_text(child))
        elif hasattr(child, "children"):
            parts.append(_quote_text(child))
    return "\n".join(part for part in parts if part)
