#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/speedreader.desktop"
TEMPLATE="$ROOT/packaging/speedreader.desktop.in"

chmod +x "$ROOT/scripts/launch.sh" "$ROOT/scripts/generate-icon.sh"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"
mkdir -p "$ICON_DIR" "$DESKTOP_DIR"
"$ROOT/scripts/generate-icon.sh"
cp "$ROOT/packaging/speedreader.png" "$ICON_DIR/speedreader.png"
sed "s|@ROOT@|$ROOT|g" "$TEMPLATE" > "$DESKTOP_FILE"
chmod 644 "$DESKTOP_FILE" "$ICON_DIR/speedreader.png"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Installed: $DESKTOP_FILE"
echo "Installed icon: $ICON_DIR/speedreader.png"
