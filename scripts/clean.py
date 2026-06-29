#!/usr/bin/env python3
"""Remove build artifacts and caches for local development."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIRECTORIES = ("build", "dist", ".pytest_cache", ".ruff_cache")
CACHE_DIR_NAMES = ("__pycache__",)


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"Removed {path.relative_to(ROOT)}")


def clean_build_outputs() -> None:
    for name in DIRECTORIES:
        _remove_path(ROOT / name)


def clean_pycache(all_dirs: bool) -> None:
    search_roots = [ROOT] if all_dirs else [ROOT / "src", ROOT / "tests", ROOT / "scripts"]
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for cache_dir in search_root.rglob("__pycache__"):
            _remove_path(cache_dir)


def clean_spec_backups() -> None:
    for spec_backup in ROOT.glob("*.spec.bak"):
        _remove_path(spec_backup)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean EasiFlux Desktop build artifacts.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also remove __pycache__ directories across the repository.",
    )
    args = parser.parse_args()

    clean_build_outputs()
    clean_pycache(all_dirs=args.all)
    clean_spec_backups()
    print("Clean completed.")


if __name__ == "__main__":
    main()
