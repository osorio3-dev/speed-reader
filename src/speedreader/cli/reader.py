"""RSVP display loop for speedreader-cli — ANSI ORP highlighting, no Qt."""

from __future__ import annotations

import shutil
import sys
import time
from typing import Optional

import colorama

from speedreader.core.engine import ReadingEngine
from speedreader.core.orp import optimal_recognition_index


colorama.init()


def format_word_ansi(word: str) -> str:
    """Return ``word`` with the ORP letter highlighted in ANSI bold+yellow.

    The ORP (Optimal Recognition Point) letter is wrapped in SGR codes
    ``\\033[1;33m`` (bold yellow) and ``\\033[0m`` (reset), placing the
    highlight on the most-recognizable letter for speed reading.

    Pure function — no side effects, trivially testable.
    """
    if not word:
        return ""
    index = optimal_recognition_index(word)
    before = word[:index]
    highlighted = word[index]
    after = word[index + 1 :]
    return f"{before}\033[1;33m{highlighted}\033[0m{after}"


def rsvp_display(
    engine: ReadingEngine,
    *,
    wpm: int | None = None,
    max_words: int | None = None,
) -> None:
    """Run the RSVP loop, writing each word to *stdout*.

    Parameters
    ----------
    engine:
        A :class:`ReadingEngine` whose segments have already been loaded
        via ``engine.load(segments)``.
    wpm:
        Optional WPM override applied to the engine before starting.
    max_words:
        If set, stop the loop after this many displayed words (useful for
        testing without blocking on a full text).
    """
    if wpm is not None:
        engine.wpm = wpm

    width = shutil.get_terminal_size().columns
    displayed = 0

    while not engine.is_finished:
        word = engine.current_word
        if word:
            display = format_word_ansi(word)
            # Centre the word in the terminal line
            visible_len = _visible_length(display)
            padding = max(0, (width - visible_len) // 2)
            sys.stdout.write(f"\r{' ' * padding}{display}")
            sys.stdout.flush()

        interval_s = engine.interval_ms() / 1000.0
        engine.advance()
        displayed += 1

        if max_words is not None and displayed >= max_words:
            break

        time.sleep(interval_s)

    # Clear the RSVP line before returning
    sys.stdout.write("\r" + " " * width + "\r")
    sys.stdout.flush()


def _visible_length(ansi_text: str) -> int:
    """Return the visible character length of text containing ANSI codes."""
    import re

    return len(re.sub(r"\033\[[0-9;]*m", "", ansi_text))
