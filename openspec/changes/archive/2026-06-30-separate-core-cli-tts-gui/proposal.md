# Proposal: Separate Core, CLI, TTS, and GUI

## Intent

`MainWindow` is a 765-line God class mixing widget layout, playback state, TTS orchestration, settings persistence, and import logic. This blocks engine reuse and a headless CLI. We will extract a Qt-free `core/` package, add a `speedreader-cli` entry point, split MainWindow into controller + view, and move Piper TTS off the main thread.

## Target Users

GUI users keep `speedreader`; terminal users read via `speedreader-cli` without PySide6; maintainers extend importers/speech without touching the GUI.

## Scope

### In Scope
- Extract pure modules into `src/speedreader/core/`.
- Define `SettingsProtocol` and `ClipboardProtocol`.
- Add `speedreader-cli` using `typer`; visual reading only.
- Split MainWindow into `ReadingController` and view.
- Move Piper synthesis off the Qt main thread.

### Out of Scope
- TTS in the CLI, daemon mode, cloud TTS, new GUI features.

## Capabilities

### New
- `core-reading`, `core-import`, `core-speech`, `cli-reader`, `gui-controller`, `gui-tts-threading`.

### Modified
- None.

## Approach

Phased extraction:
1. Move pure modules to `core/`; keep thin re-export shims.
2. Add `src/speedreader/cli/` and `speedreader-cli`.
3. Pull playback state and timers out of MainWindow into `ReadingController`.
4. Move Piper synthesis into a worker thread.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/speedreader/core/` | New | Qt-free core. |
| `src/speedreader/cli/` | New | Typer CLI. |
| `src/speedreader/ui/main_window.py` | Modified | View only. |
| `pyproject.toml` | Modified | Adds `speedreader-cli`. |
| `tests/` | Modified | Core/CLI tests added. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Circular imports from shims | Med | Re-export only. |
| QSettings blocks CLI | Med | `SettingsProtocol`; CLI adapter. |
| Timer coupling brittle | Med | Controller emits signals. |
| Piper threading breaks audio | Low | Worker + signal bridge. |

## Rollback Plan

Revert phases in reverse. Each commit is autonomous, so `git revert` restores the prior state.

## Dependencies

- `typer` for CLI.
- Optional `pyperclip` for CLI clipboard.

## Acceptance Criteria

- [ ] `uv run pytest` passes after every phase.
- [ ] `speedreader` launches the GUI.
- [ ] `speedreader-cli read <file>` renders RSVP output.
- [ ] `src/speedreader/core/` has zero PySide6 imports.
- [ ] Piper TTS no longer blocks the GUI.

## Work-Unit Commits

1. `refactor(core): extract reading domain` — engine, domain, orp, profiles; shims.
2. `refactor(core): extract importers and speech protocol`.
3. `feat(cli): add speedreader-cli`.
4. `refactor(gui): split playback state into ReadingController`.
5. `perf(tts): move Piper synthesis off main thread`.
