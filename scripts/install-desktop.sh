#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/speedreader.desktop"
TEMPLATE="$ROOT/packaging/speedreader.desktop.in"

chmod +x "$ROOT/scripts/launch.sh"
mkdir -p "$DESKTOP_DIR"
sed "s|@ROOT@|$ROOT|g" "$TEMPLATE" > "$DESKTOP_FILE"
chmod 644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo "Installed: $DESKTOP_FILE"
