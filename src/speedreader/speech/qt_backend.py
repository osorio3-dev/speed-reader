"""QTextToSpeech backend using the system offline engine."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject
from PySide6.QtTextToSpeech import QTextToSpeech

from speedreader.core.speech import SpeechCapabilities
from speedreader.speech.rate import wpm_to_qt_rate


class QtSpeechBackend(QObject):
    """Speak text with Qt's QTextToSpeech (eSpeak on Linux)."""

    def __init__(self) -> None:
        super().__init__()
        self._tts = QTextToSpeech()
        self._finished_callback: Optional[Callable[[], None]] = None
        self._audio_started_callback: Optional[Callable[[], None]] = None
        self._was_speaking = False
        self._announced_start = False
        self._tts.stateChanged.connect(self._on_state_changed)
        self._select_spanish_locale()

    @property
    def name(self) -> str:
        return "Qt"

    @property
    def capabilities(self) -> SpeechCapabilities:
        return SpeechCapabilities(
            phrase_sync=False,
            streaming=False,
            needs_key=False,
            max_chars_per_speak=None,
        )

    def set_rate_from_wpm(self, wpm: int, pace_multiplier: float = 1.0) -> None:
        self._tts.setRate(wpm_to_qt_rate(wpm, pace_multiplier=pace_multiplier))

    def set_finished_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._finished_callback = callback

    def set_audio_started_callback(
        self, callback: Optional[Callable[[], None]]
    ) -> None:
        self._audio_started_callback = callback

    def speak(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            self._emit_finished()
            return
        self._was_speaking = False
        self._announced_start = False
        self._tts.say(cleaned)

    def stop(self) -> None:
        self._was_speaking = False
        self._announced_start = False
        self._tts.stop()

    def _select_spanish_locale(self) -> None:
        for locale in self._tts.availableLocales():
            if locale.name().startswith("es"):
                self._tts.setLocale(locale)
                for voice in self._tts.availableVoices():
                    if voice.locale().name().startswith("es"):
                        self._tts.setVoice(voice)
                        return
                return

    def _on_state_changed(self, state: QTextToSpeech.State) -> None:
        if state == QTextToSpeech.State.Speaking:
            self._was_speaking = True
            if not self._announced_start:
                self._announced_start = True
                if self._audio_started_callback is not None:
                    self._audio_started_callback()
            return
        if state == QTextToSpeech.State.Ready and self._was_speaking:
            self._was_speaking = False
            self._announced_start = False
            self._emit_finished()

    def _emit_finished(self) -> None:
        if self._finished_callback is not None:
            self._finished_callback()
