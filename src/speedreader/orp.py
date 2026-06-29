"""Optimal Recognition Point (ORP) helpers for RSVP display."""

from __future__ import annotations

import html
import re

_LETTER_POSITIONS = re.compile(r"\w", flags=re.UNICODE)


def optimal_recognition_index(word: str) -> int:
    """Return the character index of the ORP within ``word``."""
    letter_positions = [match.start() for match in _LETTER_POSITIONS.finditer(word)]
    if not letter_positions:
        return 0

    core_len = len(letter_positions)
    if core_len <= 1:
        target = 0
    elif core_len <= 5:
        target = 1
    elif core_len <= 9:
        target = 2
    elif core_len <= 13:
        target = 3
    else:
        target = 4

    return letter_positions[min(target, core_len - 1)]


def format_word_with_orp(word: str, highlight_color: str = "#e67e22") -> str:
    """Return HTML that highlights the ORP letter in ``word``."""
    if not word:
        return ""

    index = optimal_recognition_index(word)
    before = html.escape(word[:index])
    highlighted = html.escape(word[index])
    after = html.escape(word[index + 1 :])
    return (
        f'{before}<span style="color:{highlight_color}; font-weight:700;">'
        f"{highlighted}</span>{after}"
    )
