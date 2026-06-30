"""Verify core speech modules load without loading PySide6.

This test runs in a subprocess to get a clean Python process
where the parent conftest hasn't already imported PySide6.
"""

import subprocess
import sys
import textwrap


def test_core_speech_modules_load_without_qt() -> None:
    """Import core.speech and core.protocols, verify no PySide6 loaded."""
    code = textwrap.dedent("""\
        import sys

        # Import core speech and protocol modules
        from speedreader.core import speech
        from speedreader.core import protocols

        # Verify no PySide6 loaded
        assert "PySide6" not in sys.modules, (
            f"PySide6 IS loaded after core speech import: "
            f"{sys.modules.get('PySide6')}"
        )
        assert "PySide6.QtCore" not in sys.modules
        assert "PySide6.QtWidgets" not in sys.modules

        # Sanity check: SpeechBackend protocol is accessible
        from speedreader.core.speech import SpeechBackend

        # Sanity check: protocols are accessible
        from speedreader.core.protocols import SettingsProtocol, ClipboardProtocol

        print("OK: All core speech modules loaded without Qt")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"Core speech modules failed to load without Qt:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
