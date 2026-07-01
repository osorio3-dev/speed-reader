# core-reading Specification

## Purpose

Extract the RSVP reading domain models, engine, ORP helpers, and reading profiles into a Qt-free `src/speedreader/core/` package. The package MUST have zero PySide6 imports. Thin re-export shims at the old locations MUST preserve backward compatibility for GUI and CLI consumers.

## Requirements

### Requirement: Qt-Free Core Package

All modules moved into `src/speedreader/core/` MUST NOT import PySide6. The package tree MUST contain only pure Python (stdlib + mistletoe for type references).

#### Scenario: Core modules load without Qt

- GIVEN the `src/speedreader/core/` package
- WHEN importing `core.domain`, `core.engine`, `core.orp`, and `core.profiles`
- THEN no `PySide6` module is loaded in the process

#### Scenario: Re-export shim resolves correctly

- GIVEN existing code at `speedreader/engine.py`
- WHEN the shim re-exports `ReadingEngine` from `speedreader.core.engine`
- THEN `speedreader.engine.ReadingEngine` IS the same class as `speedreader.core.engine.ReadingEngine`

### Requirement: Domain Models

`TextSegment`, `SegmentKind`, and `WordToken` MUST be defined in `core/domain.py` without Qt references.

#### Scenario: TextSegment carries content and kind

- GIVEN a `TextSegment(content="Hello", kind=SegmentKind.PARAGRAPH)`
- WHEN accessing `.content` and `.kind`
- THEN they return `"Hello"` and `SegmentKind.PARAGRAPH`

### Requirement: RSVP Engine

`ReadingEngine` MUST be defined in `core/engine.py` and operate on `TextSegment` lists.

#### Scenario: Engine advances through loaded words

- GIVEN a `ReadingEngine(wpm=300)` loaded with two segments
- WHEN calling `advance()` repeatedly
- THEN each call returns the next word, and `is_finished` is `True` after the last word

### Requirement: ORP Helpers

`optimal_recognition_index` and `format_word_with_orp` MUST live in `core/orp.py`.

#### Scenario: ORP targets the correct letter position

- GIVEN the word `"hello"`
- WHEN calling `optimal_recognition_index("hello")`
- THEN it returns `1` (the second letter for words with 5 letters)

### Requirement: Reading Profiles

`ReadingProfile`, `READING_PROFILES`, and pace multiplier functions MUST be in `core/profiles.py`.

#### Scenario: Visual pace multiplier returns profile-specific value

- GIVEN a `"study"` profile
- WHEN calling `visual_pace_multiplier("study", SegmentKind.HEADING)`
- THEN the result is `1.5`

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | Move `test_engine.py`, `test_orp.py`, `test_profiles.py` tests to `tests/core/` without modification |
| Qt isolation | Add `test_core_no_qt.py` — imports all `core` modules and asserts `"PySide6" not in sys.modules` |
