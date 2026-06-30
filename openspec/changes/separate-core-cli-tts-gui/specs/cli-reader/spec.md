# cli-reader Specification

## Purpose

Add a `speedreader-cli` entry point using `typer` that renders RSVP output in the terminal. The CLI MUST be visual-only (no TTS), work without PySide6 installed, and display words with ORP highlighting via terminal formatting.

## Dependencies

- `typer` for CLI framework (project dependency)
- `pyperclip` optional for clipboard reading
- Zero runtime dependency on `PySide6`

## Requirements

### Requirement: CLI Entry Point

A `speedreader-cli` console script MUST be registered in `pyproject.toml` under `[project.scripts]`. The command `speedreader-cli read <file>` MUST start RSVP display.

#### Scenario: CLI shows ORP-highlighted words

- GIVEN a text file with content `"Hello world"`
- WHEN running `speedreader-cli read /tmp/test.txt --wpm 60`
- THEN the terminal displays each word with its ORP letter highlighted, advancing at the configured WPM

#### Scenario: CLI reads from stdin

- GIVEN piped input `echo "Hello world" | speedreader-cli read --wpm 60`
- THEN the input is parsed and displayed as RSVP

#### Scenario: CLI fails gracefully on missing file

- GIVEN a non-existent file path
- WHEN running `speedreader-cli read /no/such/file`
- THEN a non-zero exit code is returned and a clear error message is printed to stderr

### Requirement: Visual-Only Reading

The CLI MUST NOT initialize or import any TTS or audio backend. It MUST use only visual RSVP display.

#### Scenario: PySide6 is not imported during CLI use

- GIVEN a system without PySide6
- WHEN running `speedreader-cli --help`
- THEN the command succeeds without ImportError

### Requirement: CLI Headless Mode

The CLI MUST store settings via a `SettingsProtocol` implementation (e.g., JSON file) and MUST NOT depend on `QSettings`.

#### Scenario: Settings persist between CLI sessions

- GIVEN a user sets WPM to 300 via settings file
- WHEN launching `speedreader-cli read file.txt`
- THEN the displayed WPM starts at 300

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | `tests/cli/` — test argument parsing, file reading, display logic with mocked terminal |
| Integration | Test with a real `.txt` file, verify stdout contains expected words |
| Qt isolation | Test that `speedreader-cli --help` succeeds with `PYTHON_DISABLE_Importer=1` for PySide6 |
