#!/usr/bin/env python3
"""Download Piper TTS voices — cross-platform replacement for download-voice.sh."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from platformdirs import user_data_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Piper TTS voices")
    parser.add_argument("voice", nargs="?", default="es_MX-ald-x_low")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available Spanish voices"
    )
    args = parser.parse_args()

    voices_dir = Path(user_data_dir("speedreader")) / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "piper.download_voices", args.voice]

    if args.list:
        cmd = [sys.executable, "-m", "piper.download_voices"]
        subprocess.run(cmd, check=True)
        return

    subprocess.run([*cmd, "--download-dir", str(voices_dir)], check=True)
    print(f"Voice installed in {voices_dir}")


if __name__ == "__main__":
    main()
