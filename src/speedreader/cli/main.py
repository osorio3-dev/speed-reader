"""speedreader-cli — headless RSVP reader powered by typer.

Usage::

    speedreader-cli read file.txt
    speedreader-cli read file.txt --wpm 300
    echo "text" | speedreader-cli read --wpm 60
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from speedreader.cli.reader import rsvp_display
from speedreader.cli.settings import JsonSettingsStore
from speedreader.core.engine import ReadingEngine
from speedreader.core.importers.file import FileImporter
from speedreader.core.importers.plain_text import PlainTextImporter

app = typer.Typer(
    name="speedreader-cli",
    help="Headless RSVP speed reader for the terminal.",
)
_settings = JsonSettingsStore()


@app.command()
def read(
    file: Optional[Path] = typer.Argument(
        None,
        help="File to read (reads from stdin when omitted).",
        exists=False,
    ),
    wpm: int = typer.Option(
        None,
        "--wpm",
        "-w",
        help="Words per minute (overrides saved preference).",
        show_default=False,
    ),
    max_words: Optional[int] = typer.Option(
        None,
        "--max-words",
        hidden=True,
        help="Stop after this many words (testing only).",
    ),
) -> None:
    """Read *file* or stdin using RSVP (Rapid Serial Visual Presentation)."""
    actual_wpm: int

    if wpm is not None:
        actual_wpm = wpm
    else:
        actual_wpm = _settings.load_wpm()

    # Read & parse input --------------------------------------------------------
    if file is not None:
        if not file.exists():
            typer.echo(f"Error: file not found: {file}", err=True)
            raise typer.Exit(code=1)
        importer = FileImporter()
        segments = importer.read(file)
    else:
        content = sys.stdin.read()
        if not content.strip():
            return  # nothing to read
        importer = PlainTextImporter()
        segments = importer.parse(content)
    engine = ReadingEngine(wpm=actual_wpm)
    engine.load(segments)

    try:
        rsvp_display(engine, max_words=max_words)
    except KeyboardInterrupt:
        pass


def main() -> None:
    app()


if __name__ == "__main__":
    main()
