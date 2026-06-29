#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
QT_QPA_PLATFORM=offscreen uv run python scripts/generate-icon.py
