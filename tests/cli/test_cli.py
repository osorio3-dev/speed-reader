"""Tests for speedreader-cli — argument parsing, RSVP display, Qt isolation."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from speedreader.cli.main import app

runner = CliRunner()


def test_format_word_ansi() -> None:
    """format_word_ansi wraps the ORP letter in ANSI bold+yellow."""
    from speedreader.cli.reader import format_word_ansi

    # "hello" has 5 alpha chars → ORP at index 1 (second letter)
    result = format_word_ansi("hello")
    assert "\033[1;33m" in result, "Should contain ANSI bold+yellow start"
    assert "\033[0m" in result, "Should contain ANSI reset"
    assert result.count("h") == 1, "h should appear once (before ORP)"
    assert "hello" in result.replace("\033[1;33m", "").replace("\033[0m", "")


def test_format_word_ansi_empty() -> None:
    """format_word_ansi returns empty string for empty input."""
    from speedreader.cli.reader import format_word_ansi

    assert format_word_ansi("") == ""


def test_help_succeeds() -> None:
    """speedreader-cli --help exits with code 0 and shows usage."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "read" in result.stdout


def test_read_missing_file_exits_with_error() -> None:
    """speedreader-cli read yields non-zero exit for a non-existent file."""
    result = runner.invoke(app, ["/no/such/file"])
    assert result.exit_code != 0
    assert "Error" in result.output or "not found" in result.output


def test_read_displays_words(tmp_path: Path) -> None:
    """read command displays file words on stdout."""
    file = tmp_path / "test.txt"
    file.write_text("Hello world")

    result = runner.invoke(
        app, ["--wpm", "9999", "--max-words", "2", str(file)],
    )
    assert result.exit_code == 0
    assert "Hello" in result.stdout.replace("\033[1;33m", "").replace("\033[0m", "")
    assert "world" in result.stdout.replace("\033[1;33m", "").replace("\033[0m", "")


def test_read_from_stdin() -> None:
    """read command reads from stdin when no file argument is given."""
    result = runner.invoke(
        app, ["--wpm", "9999", "--max-words", "2"],
        input="piped content\n",
    )
    assert result.exit_code == 0
    assert "piped" in result.stdout.replace("\033[1;33m", "").replace("\033[0m", "")


def test_no_pyside6_during_cli() -> None:
    """CLI --help works without PySide6 being loaded."""
    code = textwrap.dedent("""\
        import sys
        from typer.testing import CliRunner
        from speedreader.cli.main import app

        assert "PySide6" not in sys.modules, (
            f"PySide6 IS loaded: {sys.modules.get('PySide6')}"
        )
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        print("OK: CLI works without PySide6")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"PySide6 isolation failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
