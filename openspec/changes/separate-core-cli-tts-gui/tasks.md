# Tasks: Separate Core, CLI, TTS, and GUI

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~3800 (5 commits) |
| 400-line budget risk | High |
| Chained PRs recommended | No (commit-only) |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: High

**Note**: Commit-only delivery. Commits 1, 2, 4, 5 exceed 400 lines (moves/rewrites dominate, not new logic).

## Commit 1: `refactor(core): extract reading domain` (~950 lines)

- [x] 1.1 [RED] Write `tests/core/test_core_no_qt.py` — import core modules, assert no PySide6 loaded
- [x] 1.2 [RED] Move existing engine/orp/profiles tests to `tests/core/` (rename)
- [x] 1.3 [GREEN] Create `core/{__init__,domain,engine,orp,profiles}.py` with moved content
- [x] 1.4 [REFACTOR] Replace `domain.py`, `engine.py`, `orp.py`, `profiles.py` with shims: `from speedreader.core.X import *`
- [x] 1.5 Verify `pytest tests/core/`; old `from speedreader.engine import ReadingEngine` works

## Commit 2: `refactor(core): extract importers and speech protocol` (~680 lines)

- [x] 2.1 [RED] Write `tests/core/importers/test_importers_no_qt.py` — no PySide6 after core importers load
- [x] 2.2 [RED] Write `tests/core/test_speech_protocols_no_qt.py` — import core.speech, assert no PySide6
- [x] 2.3 [RED] Write `tests/core/test_settings_protocol.py` — dict-backed FakeSettings conforms to SettingsProtocol
- [x] 2.4 [GREEN] Create `core/protocols.py` — SettingsProtocol + ClipboardProtocol
- [x] 2.5 [GREEN] Create `core/speech.py`, `core/rate.py` — move SpeechBackend + rate helpers
- [x] 2.6 [GREEN] Create `core/importers/` — copy all importers, add ClipboardProtocol injection to ClipboardImporter
- [x] 2.7 [REFACTOR] Shim old importers + `speech/base.py`; add SettingsProtocol conformance to `settings.py`
- [x] 2.8 Verify importer tests pass at old locations via shims + `tests/core/`

## Commit 3: `feat(cli): add speedreader-cli` (~280 lines)

- [x] 3.1 [RED] Write `tests/cli/test_cli.py` — arg parsing, file/RSVP display, missing-file error, no PySide6
- [x] 3.2 [RED] Write `tests/cli/test_cli_settings.py` — JsonSettingsStore persist/load
- [x] 3.3 [GREEN] Create `cli/settings.py` — JsonSettingsStore(SettingsProtocol)
- [x] 3.4 [GREEN] Create `cli/reader.py` — RSVP loop with ORP ANSI highlighting
- [x] 3.5 [GREEN] Create `cli/main.py` — typer app (`read <file> --wpm`, stdin support)
- [x] 3.6 [GREEN] Add `speedreader-cli` script entry to `pyproject.toml`
- [x] 3.7 Verify `speedreader-cli read --wpm 60`; `pytest tests/cli/` passes

## Commit 4: `refactor(gui): split playback state into ReadingController` (~1445 lines)

- [x] 4.1 [RED] Write `tests/gui/test_reading_controller.py` — isolated controller, mock callbacks, play/pause/seek/signals
- [x] 4.2 [RED] Write `tests/gui/test_controller_view_integration.py` — MainWindow reacts to controller signals
- [x] 4.3 [GREEN] Create `ui/reading_controller.py` — QObject with word_changed/status_changed/finished/progress_changed signals; owns engine, timers, SpeechBackend
- [x] 4.4 [REFACTOR] Rewrite `ui/main_window.py` — thin view: widgets, layout, drag-drop, shortcuts only; emits play_requested/pause_requested
- [x] 4.5 Verify GUI launches; play/pause/seek works; `pytest tests/gui/` passes

## Commit 5: `perf(tts): move Piper synthesis off main thread` (~424 lines)

- [ ] 5.1 [RED] Write `tests/gui/test_tts_threading.py` — mock PiperVoice, verify worker emits audio_ready; stop cancels
- [ ] 5.2 [GREEN] Extract `PiperWorker(QObject)` in `piper_backend.py` — signals: audio_ready; slots: do_synthesize, abort
- [ ] 5.3 [GREEN] Modify `PiperSpeechBackend` — owns QThread+worker; speak() emits queued signal; generation counter discards stale audio; finished_callback via signal bridge
- [ ] 5.4 Verify `pytest tests/gui/test_tts_threading.py`; `test_speech.py` unchanged
