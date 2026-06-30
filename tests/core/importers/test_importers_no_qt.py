"""Verify core importers load without loading PySide6.

This test runs in a subprocess to get a clean Python process
where the parent conftest hasn't already imported PySide6.
"""

import subprocess
import sys
import textwrap


def test_core_importers_load_without_qt() -> None:
    """Import all core importers and verify PySide6 is NOT loaded."""
    code = textwrap.dedent("""\
        import sys

        # Import all core importer modules
        from speedreader.core.importers import file
        from speedreader.core.importers import markdown
        from speedreader.core.importers import plain_text
        from speedreader.core.importers import clipboard

        # Verify no PySide6 loaded
        assert "PySide6" not in sys.modules, (
            f"PySide6 IS loaded after core importers import: "
            f"{sys.modules.get('PySide6')}"
        )
        assert "PySide6.QtCore" not in sys.modules
        assert "PySide6.QtWidgets" not in sys.modules

        # Sanity check: core types are accessible
        from speedreader.core.importers.file import FileImporter, is_supported_file
        from speedreader.core.importers.markdown import MarkdownImporter
        from speedreader.core.importers.plain_text import PlainTextImporter
        from speedreader.core.importers.clipboard import ClipboardImporter
        from speedreader.core.protocols import ClipboardProtocol

        print("OK: All core importer modules loaded without Qt")
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"Core importer modules failed to load without Qt:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
