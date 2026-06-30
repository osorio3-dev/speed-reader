"""Verify core modules load without loading PySide6.

This test runs in a subprocess to get a clean Python process
where the parent conftest hasn't already imported PySide6.
"""

import subprocess
import sys
import textwrap


def test_core_modules_load_without_qt() -> None:
    """Import all core modules and verify PySide6 is NOT loaded."""
    code = textwrap.dedent("""\
        import sys

        # Import all core modules
        from speedreader.core import domain
        from speedreader.core import engine
        from speedreader.core import orp
        from speedreader.core import profiles

        # Verify no PySide6 loaded
        assert "PySide6" not in sys.modules, (
            f"PySide6 IS loaded after core import: {sys.modules.get('PySide6')}"
        )
        assert "PySide6.QtCore" not in sys.modules
        assert "PySide6.QtWidgets" not in sys.modules

        # Sanity check: core types are accessible
        from speedreader.core.domain import SegmentKind, TextSegment
        from speedreader.core.engine import ReadingEngine
        from speedreader.core.orp import format_word_with_orp, optimal_recognition_index
        from speedreader.core.profiles import ReadingProfile, READING_PROFILES

        print("OK: All core modules loaded without Qt")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"Core modules failed to load without Qt:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
