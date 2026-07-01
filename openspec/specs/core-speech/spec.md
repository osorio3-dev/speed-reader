# core-speech Specification

## Purpose

Define the abstract `SpeechBackend` protocol, `SettingsProtocol`, and `ClipboardProtocol` in `src/speedreader/core/`. These protocols SHALL enable CLI and GUI consumers to inject platform-specific implementations without importing Qt.

## Requirements

### Requirement: SettingsProtocol

A `SettingsProtocol` MUST be defined in `src/speedreader/core/` with methods for loading and saving WPM, TTS settings, font size, reading profile, and session. Each method MUST accept and return plain Python types (no Qt types).

#### Scenario: SettingsProtocol defines required persistence methods

- GIVEN a `SettingsProtocol` implementation
- WHEN calling `load_wpm()` and `save_wpm(400)`
- THEN the protocol contract is satisfied

#### Scenario: CLI adapter works without QSettings

- GIVEN a `SettingsProtocol` implementation backed by JSON or environment
- WHEN loading settings
- THEN no Qt modules are imported

### Requirement: ClipboardProtocol

A `ClipboardProtocol` with `text() -> str` MUST be defined in `src/speedreader/core/`. The CLI SHALL use `pyperclip` (optional dependency); the GUI SHALL use `QApplication.clipboard()`.

#### Scenario: ClipboardProtocol defines text access

- GIVEN a `text()` method returning `"clipboard content"`
- WHEN calling `read_text()`
- THEN the result is `"clipboard content"`

### Requirement: SpeechBackend Protocol

The existing `SpeechBackend` protocol MUST be moved to `src/speedreader/core/speech.py` without modification. It MUST remain a `typing.Protocol`.

#### Scenario: SpeechBackend protocol is defined without Qt

- GIVEN `from speedreader.core.speech import SpeechBackend`
- WHEN inspecting its interface
- THEN it defines `name`, `set_rate_from_wpm`, `set_finished_callback`, `speak`, and `stop`

### Requirement: Rate Helpers

`wpm_to_length_scale` and `wpm_to_qt_rate` MUST be moved to `src/speedreader/core/`.

#### Scenario: Rate helpers are pure functions

- GIVEN `wpm_to_length_scale(300)`
- THEN the result is `1.0`

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | `test_settings_protocol.py` tests with a dict-backed `FakeSettings` |
| Qt isolation | `test_speech_protocols_no_qt.py` — import all core speech modules, assert no PySide6 |
