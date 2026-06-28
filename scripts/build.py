#!/usr/bin/env python3
"""Local PyInstaller build helper for EasiFlux Desktop."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SPEC_FILES = {
    "onedir": "easiflux_desktop.spec",
    "onefile": "easiflux_desktop_onefile.spec",
}

OUTPUT_HINTS = {
    "onedir": ROOT / "dist" / "EasiFlux" / "EasiFlux.exe",
    "onefile": ROOT / "dist" / "EasiFlux.exe",
}


def _run(command: list[str], *, cwd: Path) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EasiFlux Desktop with PyInstaller.")
    parser.add_argument(
        "--mode",
        choices=("onedir", "onefile"),
        default="onedir",
        help="PyInstaller build mode (default: onedir).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous build artifacts before building.",
    )
    args = parser.parse_args()

    if args.clean:
        _run([sys.executable, str(ROOT / "scripts" / "clean.py")], cwd=ROOT)

    spec_name = SPEC_FILES[args.mode]
    spec_path = ROOT / spec_name
    if not spec_path.exists():
        raise SystemExit(f"Spec file not found: {spec_path}")

    _run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", spec_name],
        cwd=ROOT,
    )

    output_path = OUTPUT_HINTS[args.mode]
    if not output_path.exists():
        raise SystemExit(f"Build output not found: {output_path}")

    print(f"Build completed: {output_path}")


if __name__ == "__main__":
    main()
