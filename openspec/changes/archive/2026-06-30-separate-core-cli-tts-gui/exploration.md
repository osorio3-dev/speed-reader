## Exploration: separate-core-cli-tts-gui

### Current State

Speedreader is a monolithic PySide6 desktop app where `src/speedreader/ui/main_window.py` (765 lines) acts as a God class owning widget construction, the playback state machine, TTS lifecycle orchestration, ReadingEngine control, settings persistence, file/clipboard/drag-and-drop import, keyboard shortcuts, and fullscreen handling. There is no CLI, no separation between core domain logic and UI, and TTS synthesis runs on the Qt main thread blocking UI updates.

### Affected Areas

- `src/speedreader/ui/main_window.py` — **765-line God class** mixing 8+ responsibilities (widget layout, playback state machine, TTS orchestration, engine control, settings persistence, import orchestration, shortcuts, fullscreen). Primary target for decomposition.
- `src/speedreader/engine.py` — **Pure domain logic** (no Qt imports at all). Ready for core extraction as-is. 285 lines.
- `src/speedreader/domain.py` — **Pure domain models** (`SegmentKind`, `TextSegment`). No Qt. 30 lines.
- `src/speedreader/orp.py` — **Pure ORP formatting** (only `html`, `re`). 44 lines.
- `src/speedreader/profiles.py` — **Pure profile data** (only `dataclasses`, `domain.py`). 105 lines.
- `src/speedreader/settings.py` — **Mixed**: pure functions (`clamp_wpm`, `snap_wpm`, `clamp_font_size`, `ReadingSession`) are Qt-free; `SettingsStore` depends on `PySide6.QtCore.QSettings`. Line 9: `from PySide6.QtCore import QSettings`.
- `src/speedreader/importers/clipboard.py` — **Mostly pure** but lazy-imports `QApplication` in `_default_clipboard()` at line 43 (`from PySide6.QtWidgets import QApplication`). The class accepts injection via `_ClipboardLike` protocol.
- `src/speedreader/importers/file.py` — **Pure**. No Qt imports. 37 lines.
- `src/speedreader/importers/markdown.py` — **Pure**. No Qt imports. 162 lines.
- `src/speedreader/importers/plain_text.py` — **Pure**. No Qt imports. 20 lines.
- `src/speedreader/speech/piper_backend.py` — **Heavy Qt coupling**: imports `PySide6.QtCore.QObject, QByteArray, QBuffer, QIODevice, QTimer, Slot` and `PySide6.QtMultimedia.QAudio, QAudioFormat, QAudioSink, QMediaDevices`. Runs synthesis on main thread. 124 lines.
- `src/speedreader/speech/qt_backend.py` — **Heavy Qt coupling**: `PySide6.QtCore.QObject`, `PySide6.QtTextToSpeech.QTextToSpeech`. 66 lines.
- `src/speedreader/speech/factory.py` — **Light Qt coupling** via `QT_VOICE_ID` import. Factory creates backends.
- `src/speedreader/speech/rate.py` — **Pure** math helpers. No Qt. 27 lines.
- `src/speedreader/speech/voices.py` — **Pure** discovery/selection. No Qt. 90 lines.
- `src/speedreader/speech/base.py` — **Pure Protocol**. No Qt. 25 lines.
- `src/speedreader/app.py` — QApplication bootstrap. 21 lines.
- `src/speedreader/__init__.py` — Public API. No Qt. 18 lines.
- `src/speedreader/paths.py` — Pure path logic. 14 lines.
- `pyproject.toml` — Entry point `speedreader = "speedreader.app:main"` hardcodes GUI launch. Line 24.
- `tests/test_main_window.py` — Requires `qapp` fixture (QApplication).
- `tests/test_settings.py` — Requires `PySide6.QtCore.QSettings`.
- `tests/test_speech.py` — Tests factory (needs QApp for Qt backend) but rate/voices tests are pure.

### Approaches

1. **Big Bang rewrite** — Create `core/`, `cli/`, refactor GUI, and thread TTS in one massive change
   - Pros: Single conceptual pass, no intermediate states to manage
   - Cons: **Extreme risk**: probably 1500+ lines changed, impossible to review, breaks tests for weeks, zero deployable intermediate states
   - Effort: **High** (High risk)

2. **Phased extraction with intermediary controller** — Extract core first (zero behavior change), then add CLI (new code, no regression), then refactor MainWindow into view + controller, then thread TTS
   - Pros: Each phase is independently testable, reversible, reviewable under 400 lines; Core extraction requires **NO changes to existing tests** (pure moves); CLI is additive, not modifying existing paths
   - Cons: Takes more steps; need to maintain backward compat of import paths during migration (or use lazy imports)
   - Effort: **Medium** (Low risk)

3. **Extract controller only, defer CLI** — Pull playback state machine + TTS orchestration into `ReadingController`; keep the rest of MainWindow as thin view; defer CLI to later change
   - Pros: Faster immediate payoff (smallest MainWindow); lower scope
   - Cons: Leaves core mixed with GUI dependency; CLI would need a second extraction pass later; less clean architecture
   - Effort: **Medium** (Medium risk)

### Recommendation

**Approach 2: Phased extraction with intermediary controller.** Here's the proposed commit/work-unit plan:

1. **`core/` package extraction** — Move `domain.py`, `engine.py`, `orp.py`, `profiles.py`, `importers/` (minus clipboard lazy Qt), `speech/base.py`, `speech/rate.py`, `speech/voices.py` into `src/speedreader/core/`. Add `core/protocols.py` for abstract SettingsStore protocol and abstract Clipboard protocol. Backward-compat re-exports in original locations so nothing breaks. **Pure move + adapters.**
2. **CLI add** — New `src/speedreader/cli/` package with `typer` entry point. Uses core directly. Adds `pyproject.toml` script `speedreader-read`. **Additive only.**
3. **MainWindow controller extraction** — Pull playback state machine, timer coordination, and TTS orchestration into `ReadingController` (signals-based). MainWindow becomes view-only. Requires SettingsStore adapter to implement new protocol.
4. **TTS off-main-thread** — Move `PiperSpeechBackend` synthesis into `QThread` or subprocess via signal/slot bridge. Keep Qt backend as-is (it's already async via QTextToSpeech signals).

### Risks

- **Risk 1: Circular imports during `core/` extraction.** The existing `__init__.py` re-exports `ReadingEngine`, `FileImporter`, etc. If `core/` needs to import from `settings.py` and `settings.py` imports from `profiles.py`, the dependency graph is currently flat (`settings → profiles` is fine). The risk is adding backward-compat shims that create cycles. **Mitigation**: Keep shims as thin re-export modules (e.g., `speedreader/engine.py` becomes `from speedreader.core.engine import *`) — no new cross-imports.
- **Risk 2: `SettingsStore` QSettings dependency blocks core extraction.** The pure functions (`clamp_wpm`, `snap_wpm`, etc.) and `ReadingSession` dataclass can move to core, but `SettingsStore` needs `QSettings`. **Mitigation**: Define `SettingsProtocol` in `core/protocols.py`; have existing `SettingsStore` implement it; CLI uses a JSON/INI based impl.
- **Risk 3: `ClipboardImporter` lazy Qt import prevents pure core import of importers.** The `ClipboardImporter._default_clipboard()` imports `QApplication` inside a method, not at module level, so importing the class itself doesn't pull Qt in. The CLI would need a different clipboard mechanism (pyperclip). **Mitigation**: `core` imports `ClipboardImporter` as a reference; CLI creates its own `CliClipboardImporter` that uses `pyperclip` or input stream.
- **Risk 4: MainWindow's `_uses_phrase_tts()` and timer coordination logic is tightly coupled to both Qt timers and Piper's naming convention.** Extracting this to a controller requires rethinking how timers interact with signals. **Mitigation**: The controller emits signals (e.g., `position_changed(index)`, `finished()`) that the view connects to; timers live in the controller.
- **Risk 5: Speech backends inherit `QObject`.** To make the speech protocol pure, the backends must remain in the GUI layer. The core defines only the `SpeechBackend` Protocol. CLI speech uses a different mechanism (e.g., `subprocess` calls to `piper` binary or `espeak`). **Acceptable** — this is the right boundary.

### Ready for Proposal

**Yes.** The boundary analysis is complete. The orchestrator should proceed to `sdd-propose` with the phased approach (Approach 2). Key message to user: the extraction is safe because:
- Pure modules (`domain`, `engine`, `orp`, `profiles`, `rate`, `voices`, `markdown importer`, `plain_text importer`, `file importer`) already exist and need only a directory move + re-export shims.
- Qt coupling is limited to `SettingsStore`, `ClipboardImporter._default_clipboard()`, the speech backends, and all of `ui/`.
- The 765-line MainWindow can lose ~300 lines of controller logic while keeping ~465 lines of pure view/display code.
