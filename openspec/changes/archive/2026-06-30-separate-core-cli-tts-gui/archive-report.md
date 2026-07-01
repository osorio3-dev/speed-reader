# Archive Report — `separate-core-cli-tts-gui`

**Date**: 2026-06-30  
**Archive Path**: `openspec/changes/archive/2026-06-30-separate-core-cli-tts-gui/`  
**Mode**: OpenSpec (filesystem)

---

## Verification Gates

| Gate | Result | Evidence |
|------|--------|----------|
| 5 work-unit commits in git history | ✅ | `4e2f546` (core-reading), `3022428` (core-import), `fc11311`+`e9407af` (cli), `066cba8` (gui-controller), `109a81b` (tts-threading) |
| All 5 acceptance criteria met | ✅ | See AC table below |
| All tests pass | ✅ | `uv run pytest`: 140 passed in 34.59s |
| All verification CRITICAL issues resolved | ✅ | C1 (entry point): fixed `0b1cff5`; C2 (apply-progress): fixed `fdebe9d` |
| All verification WARNING issues resolved | ✅ | W1 (PySide6 in core): fixed `3a51f01`; W2 (CLI spec mismatch): fixed `ab94fe4` |
| All tasks completed | ✅ | 29/29 tasks checked, 0 stale unchecked |

## Acceptance Criteria (from proposal)

| # | Criterion | Status | Details |
|---|-----------|--------|---------|
| 1 | `uv run pytest` passes after every phase | ✅ | 140 tests pass |
| 2 | `speedreader` launches the GUI | ✅ | Entry point at `pyproject.toml:25` |
| 3 | `speedreader-cli read <file>` renders RSVP output | ✅ | Entry point at `pyproject.toml:26`; spec updated to match actual CLI pattern |
| 4 | `src/speedreader/core/` has zero PySide6 imports | ✅ | Qt fallback removed from `ClipboardImporter` (commit `3a51f01`) |
| 5 | Piper TTS no longer blocks the GUI | ✅ | `QThread` worker + generation counter in `piper_backend.py` (commit `109a81b`) |

## Fix Commits (post-verify, pre-archive)

| Commit | Fixes | Description |
|--------|-------|-------------|
| `0b1cff5` | C1 | Register `speedreader-cli` entry point in `pyproject.toml` |
| `fdebe9d` | C2 | Add apply-progress artifact |
| `3a51f01` | W1 | Remove Qt fallback from core `ClipboardImporter` |
| `ab94fe4` | W2/S2 | Update CLI spec scenarios to match implementation |

## Specs Synced

| Domain | Action | Requirements |
|--------|--------|-------------|
| core-reading | Created | Qt-free core package, domain models, RSVP engine, ORP helpers, reading profiles |
| core-import | Created | File/Markdown/PlainText importers, ClipboardProtocol, zero-Qt importers |
| core-speech | Created | SettingsProtocol, ClipboardProtocol, SpeechBackend protocol, rate helpers |
| cli-reader | Created | Typer CLI entry, RSVP display, ORP ANSI highlighting, JSON settings |
| gui-controller | Created | ReadingController signals, thin view pattern, signal interface |
| gui-tts-threading | Created | QThread Piper worker, generation counter, signal bridge |

## Archive Contents

- `proposal.md` ✅ — 5 acceptance criteria, 5 work-unit commits
- `specs/` ✅ — 6 domain specs (core-reading, core-import, core-speech, cli-reader, gui-controller, gui-tts-threading)
- `design.md` ✅ — 7 architecture decisions, package structure, threading design
- `tasks.md` ✅ — 29/29 tasks complete
- `apply-progress.md` ✅ — TDD cycle evidence for all 5 commits
- `verify-report.md` ✅ — Final verdict: PASS (all issues resolved)
- `archive-report.md` ✅ — This file

## Source of Truth Updated

`openspec/specs/` now contains 6 domain specs reflecting the extracted architecture:
- `openspec/specs/core-reading/spec.md`
- `openspec/specs/core-import/spec.md`
- `openspec/specs/core-speech/spec.md`
- `openspec/specs/cli-reader/spec.md`
- `openspec/specs/gui-controller/spec.md`
- `openspec/specs/gui-tts-threading/spec.md`

## SDD Cycle Complete

The change `separate-core-cli-tts-gui` has been fully planned, implemented, verified, and archived.
