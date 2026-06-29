"""Filesystem paths used by the speedreader package."""

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent


def app_icon_path() -> Path:
    """Return the path to the application icon bundled with the project."""
    svg_path = _PROJECT_ROOT / "packaging" / "speedreader.svg"
    if svg_path.is_file():
        return svg_path
    return _PROJECT_ROOT / "packaging" / "speedreader.png"
