"""Launch the Chess Analyser monitoring/control panel as a standalone tool."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chess_analyser.config import DEFAULT_SETTINGS
from chess_analyser.logging import setup_logging
from chess_analyser.ui import MainWindow


def main() -> None:
    """Start the monitoring/control panel."""
    setup_logging(
        level=getattr(logging, DEFAULT_SETTINGS.log_level),
        console=True,
    )
    MainWindow().run()


if __name__ == "__main__":
    main()
