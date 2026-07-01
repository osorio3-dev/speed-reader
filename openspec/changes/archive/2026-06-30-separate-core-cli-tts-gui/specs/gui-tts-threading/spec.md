# gui-tts-threading Specification

## Purpose

Move Piper TTS synthesis off the Qt main thread so audio generation does not block the GUI event loop. The `PiperSpeechBackend` SHALL run synthesis in a `QThread` worker and signal the GUI thread when audio is ready for playback.

## Requirements

### Requirement: Worker Thread for Piper Synthesis

The `PiperSpeechBackend.speak()` method MUST delegate ONNX model inference to a `QThread` worker. The worker SHALL emit a `audio_ready` signal with synthesized audio data, which the main thread consumes to start `QAudioSink` playback.

#### Scenario: Synthesis runs without blocking the GUI

- GIVEN a running GUI with Piper backend
- WHEN `speak("long text...")` is called
- THEN the call returns immediately
- AND synthesis starts on a worker thread
- AND `QAudioSink` playback begins when the worker emits `audio_ready`

#### Scenario: Stop cancels in-flight synthesis

- GIVEN a long utterance being synthesized on the worker thread
- WHEN `stop()` is called
- THEN the worker thread is notified to abort
- AND no `audio_ready` signal is emitted for the cancelled generation

### Requirement: Thread-Safe Callback Bridge

The `finished_callback` MUST be invoked on the main thread after playback completes. A `QObject` signal bridge SHALL relay the worker's completion event to the main thread.

#### Scenario: Finished callback fires on main thread

- GIVEN a `PiperSpeechBackend` with a finished callback
- WHEN audio playback ends
- THEN the callback is invoked on the Qt main thread

### Requirement: Backward-Compatible API

The `SpeechBackend` protocol MUST NOT change. Existing synchronisation logic (`set_finished_callback`, `stop`) MUST work identically from the caller's perspective.

#### Scenario: Non-Piper backends (QtSpeechBackend) unchanged

- GIVEN a `QtSpeechBackend` that does not need threading
- WHEN speaking text
- THEN it continues to work synchronously on the main thread without modification

## Test Expectations

| Area | Expectation |
|------|-------------|
| Unit tests | `tests/gui/test_tts_threading.py` — test worker thread lifecycle with mocked Piper voice |
| Integration | Verify GUI remains responsive during long synthesis (e.g., 100+ word passage) |
| Regression | Existing `test_speech.py` tests MUST pass without modification |
