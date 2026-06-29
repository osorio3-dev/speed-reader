#!/usr/bin/env python3
"""Render packaging/speedreader.svg to a 256x256 PNG."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    svg_path = root / "packaging" / "speedreader.svg"
    png_path = root / "packaging" / "speedreader.png"
    if not svg_path.is_file():
        print(f"Missing SVG icon: {svg_path}", file=sys.stderr)
        return 1

    app = QApplication([])
    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        print(f"Invalid SVG icon: {svg_path}", file=sys.stderr)
        return 1

    size = QSize(256, 256)
    image = QImage(size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    if not image.save(str(png_path), "PNG"):
        print(f"Failed to write PNG: {png_path}", file=sys.stderr)
        return 1

    print(f"Wrote {png_path} ({png_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
