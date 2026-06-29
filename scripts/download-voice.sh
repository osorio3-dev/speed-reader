#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VOICES_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/speedreader/voices"
VOICE="${1:-es_MX-ald-x_low}"

cd "$ROOT"
mkdir -p "$VOICES_DIR"

if [[ "${1:-}" == "--list" || "${1:-}" == "-l" ]]; then
  uv run --extra tts python -m piper.download_voices | rg '^es_'
  exit 0
fi

uv run --extra tts python -m piper.download_voices "$VOICE" --download-dir "$VOICES_DIR"
echo "Voice installed in $VOICES_DIR"
