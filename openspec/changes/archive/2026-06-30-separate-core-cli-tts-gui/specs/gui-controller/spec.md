# gui-controller Specification

## Purpose

Split playback state, timer logic, and TTS orchestration out of `MainWindow` into a `ReadingController` class. The view (`MainWindow`) SHALL remain a thin widget layer that emits user events and receives signals. The controller MUST own the `ReadingEngine`, `QTimer` instances, and `SpeechBackend`.

## Requirements

### Requirement: ReadingController

A `ReadingController` class MUST encapsulate all playback state (`_playing`, `_timer`, `_phrase_timer`, `_phrase_word_offset`), reading session management, and TTS lifecycle currently in `MainWindow`. It SHALL communicate with the view via signals/callbacks.

#### Scenario: Controller handles play/pause without view knowledge

- GIVEN a `ReadingController` configured with an engine and speech backend
- WHEN `play()` is called
- THEN the controller starts the RSVP timer and emits a `word_changed` signal on each tick
- AND calling `pause()` stops the timer and speech

#### Scenario: Controller owns source and session state

- GIVEN segments loaded into the controller
- WHEN the reading finishes
- THEN the controller emits a `finished` signal

### Requirement: View Becomes Thin Widget Layer

`MainWindow` MUST only create widgets, wire signals from `ReadingController`, and update UI elements in response to controller signals. It MUST NOT own `ReadingEngine`, `QTimer`, or speech lifecycle.

#### Scenario: View receives signals instead of direct engine access

- GIVEN a `MainWindow` connected to a `ReadingController`
- WHEN the user presses Play
- THEN the window emits a `play_requested` signal
- AND the controller starts playback
- AND the window updates the word label via a `word_changed` signal handler

### Requirement: Signal Interface

The controller MUST expose the following signals:

| Signal | Payload | Emitted When |
|--------|---------|-------------|
| `word_changed` | `word: str` | RSVP tick advances to a new word |
| `status_changed` | `text: str` | Status line should update |
| `finished` | `None` | All words consumed |
| `progress_changed` | `position: int, total: int` | Position or total changes |

#### Scenario: Signal payload types are correct

- GIVEN a `ReadingController` emitting `word_changed`
- WHEN the signal fires
- THEN the payload is a `str` containing the current word text

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | `tests/gui/test_reading_controller.py` — test controller in isolation with mocked view callbacks |
| Integration | `tests/gui/test_controller_view_integration.py` — test that MainWindow correctly reacts to controller signals |
| No Qt in controller | Controller module MUST NOT import `QMainWindow`, `QWidget`, or any widget class |
