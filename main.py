#!/usr/bin/env python3
"""Compatibility wrapper to run the packaged ttree Typer application."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))

from ttree.cli import app  # noqa: E402


def run() -> None:
    """Invoke the Typer CLI."""
    app()


if __name__ == "__main__":
    run()
