"""Filesystem paths used by the speedreader package."""

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent


def app_icon_path() -> Path:
    """Return the path to the application icon bundled with the project."""
    return _PROJECT_ROOT / "packaging" / "speedreader.png"
