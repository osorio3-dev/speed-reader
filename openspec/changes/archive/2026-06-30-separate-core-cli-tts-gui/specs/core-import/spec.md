# core-import Specification

## Purpose

Extract the file and Markdown importers into `src/speedreader/core/`. All importers MUST operate on `TextSegment` lists and MUST NOT import PySide6. The `ClipboardImporter` MUST support injection via `ClipboardProtocol` so it works without Qt.

## Requirements

### Requirement: Extract File Importers to Core

`FileImporter`, `MarkdownImporter`, and `PlainTextImporter` MUST be defined under `src/speedreader/core/importers/` with zero PySide6 imports. Thin re-export shims at the old locations MUST preserve compatibility.

#### Scenario: MarkdownImporter parses headings and paragraphs

- GIVEN a markdown string `"# Title\n\nBody text"`
- WHEN `MarkdownImporter().parse(source)` is called
- THEN it returns two `TextSegment` entries — one `HEADING` and one `PARAGRAPH`

#### Scenario: PlainTextImporter splits on blank lines

- GIVEN `"First para\n\nSecond para"`
- WHEN `PlainTextImporter().parse(source)` is called
- THEN it returns two `PARAGRAPH` segments

#### Scenario: FileImporter delegates by extension

- GIVEN a `.md` file path
- WHEN `FileImporter().read(path)` is called
- THEN it invokes `MarkdownImporter`

### Requirement: ClipboardProtocol

A `ClipboardProtocol` with a `text() -> str` method MUST be defined in `core/importers/`. The `ClipboardImporter` MUST accept an optional `clipboard: ClipboardProtocol` parameter.

#### Scenario: ClipboardImporter works with injected stub

- GIVEN a `ClipboardImporter(clipboard=FakeClipboard("hello"))`
- WHEN `.read()` is called
- THEN it returns a single `TextSegment(content="hello")`

#### Scenario: ClipboardImporter fails gracefully on empty clipboard

- GIVEN a `ClipboardImporter(clipboard=FakeClipboard(""))`
- WHEN `.read()` is called
- THEN it returns an empty list

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | Move `test_file_importer.py`, `test_plain_text_importer.py`, `test_markdown_importer.py` to `tests/core/importers/` |
| Qt isolation | Add `test_importers_no_qt.py` — assert no PySide6 import after loading all core importers |
| Clipboard | Add `test_clipboard_protocol.py` — test with `FakeClipboard` stub, no `QApplication` |
