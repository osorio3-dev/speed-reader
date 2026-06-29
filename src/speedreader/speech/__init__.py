"""Speech synthesis backends for TTS-driven reading."""

from speedreader.speech.base import SpeechBackend
from speedreader.speech.factory import create_speech_backend

__all__ = ["SpeechBackend", "create_speech_backend"]
