"""Tests for the Markdown importer."""

import pytest

from speedreader import MarkdownImporter, SegmentKind, TextSegment


@pytest.fixture
def importer() -> MarkdownImporter:
    return MarkdownImporter()


def test_heading(importer: MarkdownImporter) -> None:
    segments = importer.parse("# Title\n\n## Subtitle")
    assert len(segments) == 2
    assert segments[0] == TextSegment(
        content="Title", kind=SegmentKind.HEADING, level=1
    )
    assert segments[1] == TextSegment(
        content="Subtitle", kind=SegmentKind.HEADING, level=2
    )


def test_paragraph(importer: MarkdownImporter) -> None:
    segments = importer.parse("This is a paragraph.")
    assert len(segments) == 1
    assert segments[0].kind == SegmentKind.PARAGRAPH
    assert segments[0].content == "This is a paragraph."


def test_list_item(importer: MarkdownImporter) -> None:
    segments = importer.parse("- First item\n- Second item")
    assert len(segments) == 2
    assert all(s.kind == SegmentKind.LIST_ITEM for s in segments)
    assert segments[0].content == "First item"
    assert segments[1].content == "Second item"


def test_code_block_with_language(importer: MarkdownImporter) -> None:
    source = "```python\nprint('hello')\n```"
    segments = importer.parse(source)
    assert len(segments) == 1
    segment = segments[0]
    assert segment.kind == SegmentKind.CODE_BLOCK
    assert segment.language == "python"
    assert segment.content == "print('hello')\n"


def test_inline_code(importer: MarkdownImporter) -> None:
    segments = importer.parse("Use `pip install` to get started.")
    assert len(segments) == 1
    assert segments[0].kind == SegmentKind.PARAGRAPH
    assert segments[0].content == "Use pip install to get started."


def test_link_text_only(importer: MarkdownImporter) -> None:
    segments = importer.parse("Read more at [SwiftRead](https://swiftread.com).")
    assert len(segments) == 1
    assert segments[0].kind == SegmentKind.PARAGRAPH
    assert segments[0].content == "Read more at SwiftRead."


def test_blockquote(importer: MarkdownImporter) -> None:
    segments = importer.parse("> This is a quote\n> spanning two lines")
    assert len(segments) == 1
    assert segments[0].kind == SegmentKind.BLOCKQUOTE
    assert segments[0].content == "This is a quote\nspanning two lines"


def test_mixed_document(importer: MarkdownImporter) -> None:
    source = """# Intro

This is **important** and *emphasized*.

- One
- Two

```
code block
```

> A quote
"""
    segments = importer.parse(source)
    kinds = [s.kind for s in segments]
    assert kinds == [
        SegmentKind.HEADING,
        SegmentKind.PARAGRAPH,
        SegmentKind.LIST_ITEM,
        SegmentKind.LIST_ITEM,
        SegmentKind.CODE_BLOCK,
        SegmentKind.BLOCKQUOTE,
    ]
    assert segments[1].content == "This is important and emphasized."


def test_thematic_break_does_not_crash(importer: MarkdownImporter) -> None:
    segments = importer.parse("Intro text\n\n---\n\nAfter the rule")
    assert len(segments) == 2
    assert segments[0].content == "Intro text"
    assert segments[1].content == "After the rule"


def test_table_rows(importer: MarkdownImporter) -> None:
    source = "| Name | Value |\n| --- | --- |\n| One | 1 |"
    segments = importer.parse(source)
    assert len(segments) == 2
    assert segments[0].content == "Name | Value"
    assert segments[1].content == "One | 1"


def test_setext_heading(importer: MarkdownImporter) -> None:
    segments = importer.parse("Main title\n==========\n\nBody")
    assert segments[0] == TextSegment(
        content="Main title", kind=SegmentKind.HEADING, level=1
    )
    assert segments[1].content == "Body"
