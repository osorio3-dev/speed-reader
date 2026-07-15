"""Playback state and timing for RSVP reading.

Owns the ReadingEngine, QTimers, and SpeechBackend.
Emits signals so the view stays thin.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from speedreader.core.domain import SegmentKind, TextSegment
from speedreader.core.engine import ReadingEngine
from speedreader.core.orp import format_word_with_orp
from speedreader.core.speech import SpeechBackend
from speedreader.settings import SettingsStore, snap_wpm


class ReadingController(QObject):
    """Owns engine, timers, and speech backend. Emits signals for the view.

    Signals
    -------
    word_changed(str) : HTML or plain text to display in the word label.
    status_changed(str) : Machine-readable status token:
        "playing", "paused", "finished", "idle".
    finished() : Reading completed (last word reached).
    progress_changed(int, int) : (position, total) 0-indexed position.
    """

    word_changed = Signal(str)
    status_changed = Signal(str)
    finished = Signal()
    progress_changed = Signal(int, int)

    def __init__(
        self,
        engine: ReadingEngine,
        speech: SpeechBackend,
        settings: SettingsStore,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._settings = settings
        self._speech = speech
        self._speech.set_finished_callback(self._on_speech_finished)
        self._audio_started = False
        self._phrase_timer_started = False
        self._install_audio_started_callback()

        # Word-advance timer (visual-only mode)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        # Phrase-visual timer (Piper TTS mode — shows each word as spoken)
        self._phrase_timer = QTimer(self)
        self._phrase_timer.timeout.connect(self._on_phrase_visual_tick)

        # Playback state
        self._phrase_word_offset: int = 0
        self._playing: bool = False
        self._source_path: Optional[str] = None
        self._source_kind: Optional[str] = None
        self._tts_wpm: int = settings.load_tts_wpm(engine.wpm)
        self._tts_enabled: bool = settings.load_tts_enabled()
        self._apply_speech_rate()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def engine(self) -> ReadingEngine:
        return self._engine

    @property
    def speech(self) -> SpeechBackend:
        return self._speech

    @speech.setter
    def speech(self, backend: SpeechBackend) -> None:
        self._speech = backend
        self._speech.set_finished_callback(self._on_speech_finished)
        self._install_audio_started_callback()
        self._apply_speech_rate()

    def _install_audio_started_callback(self) -> None:
        """Wire audio-started callback if the backend supports it."""
        callback = getattr(self._speech, "set_audio_started_callback", None)
        if callable(callback):
            callback(self._on_audio_started)

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def tts_wpm(self) -> int:
        return self._tts_wpm

    @tts_wpm.setter
    def tts_wpm(self, value: int) -> None:
        self._tts_wpm = snap_wpm(value)

    @property
    def tts_enabled(self) -> bool:
        return self._tts_enabled

    @tts_enabled.setter
    def tts_enabled(self, value: bool) -> None:
        self._tts_enabled = value
        if not value:
            self._speech.stop()
            if self._playing and not self._engine.is_finished:
                self._timer.start(self._engine.interval_ms())
        else:
            self._apply_speech_rate()
            if self._playing:
                self._timer.stop()
                self._speak_current()

    @property
    def source_path(self) -> Optional[str]:
        return self._source_path

    @property
    def source_kind(self) -> Optional[str]:
        return self._source_kind

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(
        self,
        segments: List[TextSegment],
        source_path: Optional[str] = None,
        source_kind: Optional[str] = None,
        resume_position: Optional[int] = None,
    ) -> None:
        """Load new segments into the engine and reset playback."""
        self.stop()
        self._source_path = source_path if source_kind == "file" else None
        self._source_kind = source_kind
        self._engine.load(segments)
        if not self._engine.is_empty:
            if resume_position is not None:
                self._engine.seek(resume_position)
            else:
                self._engine.reset()
        self._emit_all()

    def play(self) -> None:
        """Start or resume playback."""
        if self._playing:
            return
        if self._engine.is_empty:
            return
        if self._engine.is_finished:
            self._engine.reset()
        self._playing = True
        if self._tts_enabled:
            self._speak_current()
        else:
            self._timer.start(self._engine.interval_ms())
        if not self._tts_enabled:
            self._emit_word()
        self.status_changed.emit("playing")

    def pause(self) -> None:
        """Pause playback."""
        if not self._playing:
            return
        self._playing = False
        self._timer.stop()
        self._stop_phrase_visual_timer()
        self._speech.stop()
        self.status_changed.emit("paused")

    def toggle(self) -> None:
        """Toggle between play and pause."""
        if self._playing:
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        """Stop playback fully (timers and speech)."""
        self._playing = False
        self._timer.stop()
        self._stop_phrase_visual_timer()
        self._speech.stop()

    def seek(self, index: int) -> None:
        """Jump to a specific word index. Stops playback."""
        self.stop()
        self._engine.seek(index)
        self._emit_word()
        self._emit_progress()

    def previous_word(self) -> None:
        """Go back one word (or one phrase in phrase mode)."""
        if self._engine.is_empty:
            return
        self.stop()
        if self._uses_phrase_tts():
            self._engine.retreat_phrase()
        else:
            self._engine.retreat()
        self._emit_word()
        self._emit_progress()

    def next_word(self) -> None:
        """Go forward one word (or one phrase in phrase mode)."""
        if self._engine.is_empty or self._engine.is_finished:
            return
        self.stop()
        if self._uses_phrase_tts():
            self._engine.advance_to_next_phrase()
        else:
            self._engine.advance()
        if self._engine.is_finished:
            self.finished.emit()
            self.word_changed.emit("Done")
            self.status_changed.emit("finished")
        else:
            self._emit_word()
        self._emit_progress()

    def set_wpm(self, value: int) -> None:
        """Set RSVP words per minute."""
        snapped = snap_wpm(value)
        self._engine.wpm = snapped
        if self._playing and not self._tts_enabled:
            self._timer.setInterval(self._engine.interval_ms())
        self._emit_progress()

    def set_tts_wpm(self, value: int) -> None:
        """Set TTS speech rate."""
        self._tts_wpm = snap_wpm(value)
        self._apply_speech_rate()
        self._emit_progress()

    def set_profile(self, profile_id: str) -> None:
        """Change the active reading profile."""
        if profile_id == self._engine.profile_id:
            return
        self._engine.set_profile(profile_id)
        self._apply_speech_rate()
        if self._playing and self._tts_enabled:
            self._phrase_timer.setInterval(
                self._engine.interval_ms_at(self._engine.position)
            )
        elif self._playing and not self._tts_enabled:
            self._timer.setInterval(self._engine.interval_ms())
        self._emit_progress()

    def set_speech_backend(self, backend: SpeechBackend) -> None:
        """Replace the speech backend (e.g. on voice change)."""
        was_playing = self._playing
        self._speech.stop()
        self._speech = backend
        self._speech.set_finished_callback(self._on_speech_finished)
        self._install_audio_started_callback()
        self._apply_speech_rate()
        self._emit_word()
        self._emit_progress()
        if was_playing and self._tts_enabled and not self._engine.is_finished:
            self._speak_current()

    def display_position(self) -> int:
        """Return the visual display position (accounts for phrase word offset)."""
        if self._phrase_timer.isActive():
            return self._engine.position + self._phrase_word_offset
        return self._engine.position

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _uses_phrase_tts(self) -> bool:
        """Return True when the backend handles multi-word phrases."""
        if not self._tts_enabled:
            return False
        caps = getattr(self._speech, "capabilities", None)
        if caps is not None:
            return bool(getattr(caps, "phrase_sync", False))
        # Backward compatibility for legacy backends without capabilities.
        name = getattr(self._speech, "name", "") or ""
        return name.startswith("Piper")

    def _apply_speech_rate(self) -> None:
        """Forward the current TTS WPM to the speech backend."""
        self._speech.set_rate_from_wpm(
            self._tts_wpm,
            self._engine.speech_pace_multiplier(),
        )

    def _should_skip_tts_for_current_unit(self) -> bool:
        return self._engine.current_segment_kind == SegmentKind.CODE_BLOCK

    # --- Speech helpers ---

    def _speak_current(self) -> None:
        """Speak the current unit (word or phrase) depending on mode."""
        if self._uses_phrase_tts():
            self._speak_current_phrase()
        else:
            self._speak_current_word()

    def _speak_current_word(self) -> None:
        if not self._playing:
            return
        if self._engine.is_finished:
            self._on_finished()
            return
        self._emit_word()
        if self._should_skip_tts_for_current_unit():
            self._on_speech_finished()
            return
        word = self._engine.current_word
        if not word:
            self._on_speech_finished()
            return
        self._apply_speech_rate()
        self._speech.speak(word)

    def _speak_current_phrase(self) -> None:
        if not self._playing:
            return
        if self._engine.is_finished:
            self._on_finished()
            return
        if self._should_skip_tts_for_current_unit():
            self._on_speech_finished()
            return
        phrase = self._engine.current_phrase_text()
        if not phrase:
            self._on_speech_finished()
            return
        self._phrase_word_offset = 0
        self._phrase_timer_started = False
        self._audio_started = False
        self._emit_word()
        self._apply_speech_rate()
        # Timer is NOT started here — it is started in _on_audio_started so
        # the visual cadence aligns with the moment the backend actually
        # begins producing audio. For backends that do not signal audio
        # start (or do so synchronously inside speak()), this still fires
        # at least once via the fallback below.
        self._speech.speak(phrase)
        if self._audio_started or not self._uses_phrase_tts():
            self._start_phrase_timer()

    def _start_phrase_timer(self) -> None:
        if self._phrase_timer_started:
            return
        self._phrase_timer_started = True
        self._phrase_timer.start(
            self._engine.interval_ms_at(self._engine.position)
        )

    def _on_audio_started(self) -> None:
        """Backend reports first audio byte; align the visual timer."""
        self._audio_started = True
        if not self._playing:
            return
        if not self._uses_phrase_tts():
            return
        self._start_phrase_timer()

    # --- Timer callbacks ---

    def _on_tick(self) -> None:
        """Visual-only mode: advance one word."""
        if self._tts_enabled:
            return
        self._engine.advance()
        self._emit_progress()
        if self._engine.is_finished:
            self._on_finished()
            return
        self._emit_word()
        self._timer.setInterval(self._engine.interval_ms())

    def _on_phrase_visual_tick(self) -> None:
        """Phrase-visual timer: advance the visual offset within the current phrase."""
        phrase_end = self._engine.phrase_end_position()
        next_index = self._engine.position + self._phrase_word_offset + 1
        if next_index >= phrase_end:
            self._phrase_timer.stop()
            return
        self._phrase_word_offset += 1
        self._emit_word()
        self._phrase_timer.setInterval(self._engine.interval_ms_at(next_index))

    def _on_speech_finished(self) -> None:
        """Callback invoked by the SpeechBackend after uttering a word/phrase."""
        if not self._playing or not self._tts_enabled:
            return
        self._stop_phrase_visual_timer()
        self._phrase_timer_started = False
        self._audio_started = False
        if self._uses_phrase_tts():
            self._engine.advance_phrase()
        else:
            self._engine.advance()
        self._emit_progress()
        if self._engine.is_finished:
            self._on_finished()
            return
        self._speak_current()

    def _on_finished(self) -> None:
        """Reading reached the end."""
        self.stop()
        self.word_changed.emit("Done")
        self.finished.emit()
        self.status_changed.emit("finished")
        self._emit_progress()

    def _stop_phrase_visual_timer(self) -> None:
        self._phrase_timer.stop()
        self._phrase_word_offset = 0

    # --- Signal emitters ---

    def _emit_word(self) -> None:
        """Emit word_changed with the appropriate display text."""
        if self._uses_phrase_tts() and self._phrase_timer.isActive():
            # Show individual word with ORP during phrase-visual tick
            token = self._engine.token_at(
                self._engine.position + self._phrase_word_offset
            )
            if token is None:
                self.word_changed.emit("Done")
                return
            self.word_changed.emit(format_word_with_orp(token.text))
        elif self._uses_phrase_tts():
            # Show the full phrase as plain text
            phrase = self._engine.current_phrase_text()
            if phrase is None:
                self.word_changed.emit("Done")
                return
            self.word_changed.emit(phrase)
        else:
            # Visual mode — show current word with ORP highlight
            word = self._engine.current_word
            if word is None:
                self.word_changed.emit("Done")
                return
            self.word_changed.emit(format_word_with_orp(word))

    def _emit_progress(self) -> None:
        """Emit progress_changed with current (position, total)."""
        if self._engine.is_empty:
            self.progress_changed.emit(0, 0)
            return
        pos = self.display_position()
        total = self._engine.word_count
        self.progress_changed.emit(pos, total)

    def _emit_all(self) -> None:
        """Emit all signals with current state."""
        self._emit_word()
        self._emit_progress()
        if self._engine.is_empty:
            self.status_changed.emit("idle")
        elif not self._playing:
            self.status_changed.emit("paused")
        else:
            self.status_changed.emit("playing")
