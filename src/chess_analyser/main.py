"""
Main application entry point for Chess Analyser.
"""

import logging
import sys
from pathlib import Path

from chess_analyser.config import DEFAULT_SETTINGS
from chess_analyser.logging import setup_logging
from chess_analyser.ui import MainWindow

logger: logging.Logger


def main(*, run_gui: bool = True) -> None:
    """
    Main application entry point.

    Initializes the application and starts the main loop.
    """
    global logger

    # Setup logging
    logger = setup_logging(
        level=getattr(logging, DEFAULT_SETTINGS.log_level),
        console=True,
    )

    logger.info("Chess Analyser starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    logger.info("Chess Analyser initialized successfully")
    if not run_gui:
        print("Chess Analyser initialized successfully")
        return

    logger.info("Starting Phase 3 Tkinter interface")
    MainWindow().run()


if __name__ == "__main__":
    main()
