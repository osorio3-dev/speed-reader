# Verification Report

**Change**: `separate-core-cli-tts-gui`  
**Mode**: Strict TDD (active), `uv run pytest`  
**Date**: 2026-06-30  
**Verdict**: **FAIL** — CRITICAL issues block archive readiness

---

## Completeness Table

| Artifact | Status | Notes |
|----------|--------|-------|
| Proposal | ✅ Found | 5 acceptance criteria |
| Specs | ✅ Found | 6 spec files (core-reading, core-import, core-speech, cli-reader, gui-controller, gui-tts-threading) |
| Design | ✅ Found | 7 architecture decisions, package structure, threading design |
| Tasks | ✅ Found | 5 work-unit commits, 27 subtasks |
| Apply-Progress | ❌ **Missing** | No apply-progress artifact found — cannot validate TDD Cycle Evidence |

---

## Build / Tests / Coverage

### Test Execution

**Command**: `uv run pytest`  
**Result**: ✅ **140 passed** in 36.82s

| Test Area | Count | Status |
|-----------|-------|--------|
| `tests/core/` | 30 | ✅ All pass |
| `tests/cli/` | 16 | ✅ All pass |
| `tests/gui/` | 50 | ✅ All pass |
| `tests/test_*.py` (legacy) | 44 | ✅ All pass (backward-compat shims work) |

### Coverage

Coverage analysis skipped — no coverage tool detected/intentionally omitted.

---

## Spec Compliance Matrix

| Spec | Scenario | Test Coverage | Status |
|------|----------|--------------|--------|
| **core-reading** | Core modules load without Qt | `test_core_no_qt.py::test_core_modules_load_without_qt` | ✅ PASS |
| **core-reading** | Re-export shim resolves correctly | `test_engine.py::test_load_and_advance` (via `speedreader.engine.*`) | ✅ PASS |
| **core-reading** | TextSegment carries content and kind | `test_engine.py` (implicit via usage) | ✅ PASS |
| **core-reading** | Engine advances through loaded words | `test_engine.py::test_load_and_advance` | ✅ PASS |
| **core-reading** | ORP targets correct letter position | `test_orp.py::test_orp_index_scales_with_word_length` | ✅ PASS |
| **core-reading** | Visual pace multiplier returns profile value | `test_profiles.py::test_study_profile_slows_headings` | ✅ PASS |
| **core-import** | MarkdownImporter parses headings/paragraphs | `test_engine.py::test_tokenize_segments_preserves_segment_kind` | ✅ PASS |
| **core-import** | PlainTextImporter splits on blank lines | `test_engine.py` (paragraph handling) | ✅ PASS |
| **core-import** | FileImporter delegates by extension | `test_engine.py::test_load_and_advance` (via file loading) | ✅ PASS |
| **core-import** | ClipboardImporter with injected stub | `test_settings_protocol.py::test_settings_protocol` (ClipboardProtocol verification) | ✅ PASS |
| **core-import** | ClipboardImporter empty clipboard | `test_settings_protocol.py` (empty FakeClipboard) | ✅ PASS |
| **core-import** | No Qt import after loading core importers | `test_importers_no_qt.py` | ✅ PASS |
| **core-speech** | SettingsProtocol defines required methods | `test_settings_protocol.py::test_settings_protocol` | ✅ PASS |
| **core-speech** | CLI adapter works without QSettings | `test_cli_settings.py::test_no_pyside6_imported_on_import` | ✅ PASS |
| **core-speech** | ClipboardProtocol defines text access | `test_settings_protocol.py` | ✅ PASS |
| **core-speech** | SpeechBackend protocol defined without Qt | `test_speech_protocols_no_qt.py` | ✅ PASS |
| **core-speech** | Rate helpers are pure functions | `test_speech.py::test_wpm_to_length_scale_inverts_wpm` | ✅ PASS |
| **cli-reader** | CLI shows ORP-highlighted words | `test_cli.py::test_read_displays_words` | ✅ PASS |
| **cli-reader** | CLI reads from stdin | `test_cli.py::test_read_from_stdin` | ✅ PASS |
| **cli-reader** | CLI fails gracefully on missing file | `test_cli.py::test_read_missing_file_exits_with_error` | ✅ PASS |
| **cli-reader** | PySide6 not imported during CLI use | `test_cli.py::test_no_pyside6_during_cli` | ✅ PASS |
| **cli-reader** | Settings persist between CLI sessions | `test_cli_settings.py::test_persistence_across_instances` | ✅ PASS |
| **gui-controller** | Controller handles play/pause | `test_reading_controller.py::test_play_sets_playing`, `test_pause_clears_playing` | ✅ PASS |
| **gui-controller** | Controller owns source and session state | `test_reading_controller.py::test_load_sets_engine_state` | ✅ PASS |
| **gui-controller** | View receives signals instead of direct engine | `test_controller_view_integration.py::test_word_changed_updates_word_label` | ✅ PASS |
| **gui-controller** | Signal payload types are correct | `test_reading_controller.py::test_word_changed_emitted_on_play` | ✅ PASS |
| **gui-tts-threading** | Synthesis runs without blocking GUI | `test_tts_threading.py::test_speak_emits_queued_signal` | ✅ PASS |
| **gui-tts-threading** | Stop cancels in-flight synthesis | `test_tts_threading.py::test_abort_during_multi_chunk_synthesis_halts` | ✅ PASS |
| **gui-tts-threading** | Finished callback fires on main thread | `test_tts_threading.py::test_speak_emits_queued_signal` (signal bridge) | ✅ PASS |
| **gui-tts-threading** | Non-Piper backends unchanged | `test_speech.py` backward-compat tests pass | ✅ PASS |

**Spec compliance**: 30/30 scenarios covered. All have passing tests.

---

## Task Completion Status

| Task | Status | Evidence |
|------|--------|----------|
| 1.1 — `test_core_no_qt.py` | ✅ Done | `tests/core/test_core_no_qt.py` exists, passes |
| 1.2 — Move engine/orp/profiles tests | ✅ Done | Tests moved to `tests/core/` via `git mv` |
| 1.3 — Create `core/` modules | ✅ Done | `core/{__init__,domain,engine,orp,profiles}.py` |
| 1.4 — Shim old modules | ✅ Done | Single-line `from speedreader.core.X import *` |
| 1.5 — Verify shims work | ✅ Done | Existing 5 `test_main_window.py` tests pass |
| 2.1 — `test_importers_no_qt.py` | ✅ Done | `tests/core/importers/test_importers_no_qt.py` exists, passes |
| 2.2 — `test_speech_protocols_no_qt.py` | ✅ Done | Exists, passes |
| 2.3 — `test_settings_protocol.py` | ✅ Done | Exists, passes |
| 2.4 — `core/protocols.py` | ✅ Done | Defines `SettingsProtocol` + `ClipboardProtocol` |
| 2.5 — `core/speech.py`, `core/rate.py` | ✅ Done | Pure Protocol + pure functions |
| 2.6 — `core/importers/` | ✅ Done | All importers migrated |
| 2.7 — Shim old importers + settings | ✅ Done | All old locations are single-line shims |
| 2.8 — Verify importers tests | ✅ Done | `tests/core/importers/` + old locations all pass |
| 3.1 — `tests/cli/test_cli.py` | ✅ Done | 7 tests, exists, passes |
| 3.2 — `tests/cli/test_cli_settings.py` | ✅ Done | 9 tests, exists, passes |
| 3.3 — `cli/settings.py` | ✅ Done | `JsonSettingsStore` implements `SettingsProtocol` |
| 3.4 — `cli/reader.py` | ✅ Done | RSVP loop with ANSI ORP highlighting |
| 3.5 — `cli/main.py` | ✅ Done | Typer app with `read` command |
| **3.6 — `speedreader-cli` script entry** | **❌ NOT DONE** | **Missing from `pyproject.toml`** — only `speedreader` is registered |
| 3.7 — Verify CLI tests | ✅ Partial | Tests pass. `speedreader-cli` command NOT available |
| 4.1 — `test_reading_controller.py` | ✅ Done | 33 tests, exists, passes |
| 4.2 — `test_controller_view_integration.py` | ✅ Done | 10 tests, exists, passes |
| 4.3 — `ui/reading_controller.py` | ✅ Done | QObject with signals, owns timers/speech |
| 4.4 — Rewrite `main_window.py` | ✅ Done | Thin view — widgets, layout, signals only |
| 4.5 — Verify GUI | ✅ Done | GUI entry point imports OK, all tests pass |
| 5.1 — `test_tts_threading.py` | ✅ Done | 7 tests, exists, passes |
| 5.2 — `PiperWorker(QObject)` | ✅ Done | Extracted in `piper_backend.py` |
| 5.3 — Threaded `PiperSpeechBackend` | ✅ Done | QThread worker, generation counter, signal bridge |
| 5.4 — Verify TTS tests | ✅ Done | `test_tts_threading.py` passes, `test_speech.py` unchanged |

**Tasks complete**: 26/27 ✅ — Task 3.6 is **CRITICAL** (core, not cleanup).

---

## Acceptance Criteria Check (from Proposal)

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `uv run pytest` passes after every phase | ✅ **PASS** | 140 tests pass in 36.82s |
| 2 | `speedreader` launches the GUI | ✅ **PASS** | `from speedreader.app import main` works; entry point registered at `pyproject.toml:25` |
| 3 | `speedreader-cli read <file>` renders RSVP output | ❌ **FAIL** | `speedreader-cli` NOT registered in `pyproject.toml`. CLI works via `python -m speedreader.cli.main` but not as a standalone command. Also, the CLI uses `@app.command()` so it works without the `read` subcommand keyword — spec scenarios say `speedreader-cli read <file>` but actual usage is `read --wpm 60 <file>` |
| 4 | `src/speedreader/core/` has zero PySide6 imports | ⚠️ **WARNING** | Most of `core/` is clean, but `core/importers/clipboard.py:38` has `from PySide6.QtWidgets import QApplication` (lazy import inside `_default_clipboard()`) |
| 5 | Piper TTS no longer blocks the GUI | ✅ **PASS** | `PiperSpeechBackend` delegates synthesis to `QThread` worker with generation counter to discard stale audio |

---

## Design Coherence

| Design Decision | Implementation | Status |
|-----------------|---------------|--------|
| D1 — Core package location: `src/speedreader/core/` | ✅ Matches | Package structure follows design exactly |
| D2 — SettingsProtocol location: `core/protocols.py` | ✅ Matches | `core/protocols.py` defines both protocols |
| D3 — ClipProtocol reuse | ✅ Matches | `ClipboardProtocol` defined in `core/protocols.py`, used by both CLI and GUI |
| D4 — CLI framework: typer | ✅ Matches | `cli/main.py` uses `typer` |
| D5 — CLI settings: JSON file | ✅ Matches | `cli/settings.py` → `JsonSettingsStore` |
| D6 — Piper threading: QThread + generation counter | ✅ Matches | `piper_backend.py` implements exact design |
| D7 — Controller signals | ✅ Matches | `ReadingController` emits `word_changed`, `status_changed`, `finished`, `progress_changed` |
| Package structure | ✅ Matches | All files follow the design tree exactly |
| Backward-compatible shims | ✅ Matches | Single-line `from core.X import *` at every old location |
| ReadingController public API | ✅ Matches | `load()`, `play()`, `pause()`, `toggle()`, `stop()`, `seek()`, `previous_word()`, `next_word()`, `set_wpm()`, `set_profile()` |

---

## Issues

### CRITICAL

| # | File | Line | Description | Recommendation |
|---|------|------|-------------|---------------|
| C1 | `pyproject.toml` | 24-25 | **Task 3.6 not completed**: `speedreader-cli` script entry is NOT registered. Only `speedreader = "speedreader.app:main"` exists. Proposal acceptance criterion 3 and CLI reader spec both require this to work as `speedreader-cli read <file>`. | Add `speedreader-cli = "speedreader.cli.main:main"` under `[project.scripts]` in `pyproject.toml` |
| C2 | *(no file)* | — | **No apply-progress artifact**: Strict TDD mode requires TDD Cycle Evidence table which lives in the apply-progress artifact. Without it, TDD compliance cannot be validated (RED/GREEN/TRIANGULATE/SAFETY NET columns). | Generate apply-progress report covering all 5 work-unit commits, or verify TDD evidence through alternative means |

### WARNING

| # | File | Line | Description | Recommendation |
|---|------|------|-------------|---------------|
| W1 | `src/speedreader/core/importers/clipboard.py` | 14, 38 | **PySide6 import in core package**: Line 14 references PySide6 in docstring; line 38 has `from PySide6.QtWidgets import QApplication` inside `_default_clipboard()`. The lazy import doesn't trigger at import time (subprocess tests pass), but the source code violates the zero-PySide6-imports rule. | Move `_default_clipboard()` (the Qt-based fallback) out of core and into the GUI layer where Qt is expected. The core `ClipboardImporter` should only accept an injected clipboard. |
| W2 | `pyproject.toml` | — | **CLI usage pattern mismatch**: The spec scenario says `speedreader-cli read /tmp/test.txt --wpm 60` but the actual implementation uses `@app.command()` without explicit subcommand routing. The CLI works as `read --wpm 60 /tmp/test.txt` (no `read` subcommand). After adding the entry point (fix C1), the CLI would be `speedreader-cli --wpm 60 /tmp/test.txt`. | Either update the spec scenarios to match the actual CLI pattern, or restructure the CLI to have explicit subcommands. The simpler fix is to update the spec. |

### SUGGESTION

| # | File | Line | Description | Recommendation |
|---|------|------|-------------|---------------|
| S1 | `tests/gui/test_reading_controller.py` | 40-104 | `_FakeSettings` includes non-protocol methods (`load_tts_voice`, `save_tts_voice`, `load_voices_dir`, `load_reading_profile_label`) that match concrete `SettingsStore` instead of `SettingsProtocol`. Creates tight test coupling. | Either add these methods to `SettingsProtocol`, or extract `_FakeSettings` to a shared test utility and minimize non-protocol methods. |
| S2 | All spec scenario docs | cli-reader spec | Spec scenarios reference `speedreader-cli read <file>` but the implementation doesn't use `read` as a subcommand. After adding the entry point, the usage would be `speedreader-cli --wpm 60 <file>`. | Update spec documentation to match the actual implementation pattern. |

---

## TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ❌ FAIL | No apply-progress artifact exists |
| All tasks have tests | ✅ 26/27 | Task 3.6 has no code change to test against |
| RED confirmed (tests exist) | ⚠️ Partial | All test files exist and are verified, except task 3.6 which has no test file for the missing entry point |
| GREEN confirmed (tests pass) | ✅ 140/140 | All tests pass on execution |
| Triangulation adequate | ✅ All | Multiple test cases per behavior; variance in expectations |
| Safety Net for modified files | ⚠️ Mixed | 5 legacy test files exist covering backward compat; moved test files retained history |

**TDD Compliance**: 3/6 checks passed — blocked by missing apply-progress artifact.

---

## Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 43 | 9 | pytest, subprocess (Qt isolation) |
| Integration | 50 | 3 | pytest, QApplication (qapp fixture), QTest |
| E2E | 0 | 0 | Not applicable |
| **Total** | **93** | **12** | — |

*(47 legacy tests excluded as they cover unchanged areas)*

---

## Assertion Quality

All test files were scanned for banned assertion patterns. No issues found:

- ✅ No tautologies (`assert True`, `expect(1).toBe(1)`)
- ✅ No orphan empty checks without companion non-empty tests
- ✅ Type-only assertions are paired with value assertions (`assert isinstance` + `assert ==` patterns)
- ✅ All tests call production code
- ✅ No ghost loops over potentially-empty collections
- ✅ Mock/assertion ratio: healthy (tests use minimal mocking appropriate to each layer)
- ✅ No CSS-class or implementation-detail coupling in assertions

**Assertion quality**: ✅ All assertions verify real behavior

---

## Risks

| Risk | Likelihood | Impact | Current State |
|------|------------|--------|---------------|
| CLI broken without entry point | **High** | Users cannot run `speedreader-cli` | Mitigated by fix C1 (add entry point) |
| PySide6 in core clipboard importer | Low | Injected clipboard works fine; lazy import only triggers if no clipboard injected | Acceptable given lazy-import pattern |
| Circular imports via shims | Low | All shims are single-layer; `core/` never imports shims | Mitigated by design |

---

## Next Actions

1. **(Required)** Add `speedreader-cli = "speedreader.cli.main:main"` to `pyproject.toml` `[project.scripts]` section
2. **(Recommended)** Move `_default_clipboard()` (Qt-dependent fallback) out of `core/importers/clipboard.py` into the GUI layer
3. **(Optional)** Update CLI spec scenarios from `speedreader-cli read <file>` to `speedreader-cli --wpm 60 <file>` to match actual implementation
4. Proceed to **sdd-archive** phase after fixes are confirmed

## Final Verdict

**FAIL** — CRITICAL issues block archive readiness:
1. Task 3.6 incomplete: `speedreader-cli` entry point missing from `pyproject.toml`
2. No apply-progress artifact for TDD Cycle Evidence validation
