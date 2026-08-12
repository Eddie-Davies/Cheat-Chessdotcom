"""
Main application entry point for Chess Analyser.
"""

import logging
import sys
from pathlib import Path

from chess_analyser.config import DEFAULT_SETTINGS
from chess_analyser.logging import setup_logging

logger: logging.Logger


def main() -> None:
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

    # TODO: Phase 1 - Initialize Stockfish engine
    # TODO: Phase 3 - Initialize UI
    # TODO: Phase 4 - Initialize screen capture
    # TODO: Phase 5+ - Initialize detection pipeline

    logger.info("Chess Analyser initialized successfully")
    logger.info("Application is ready (Phase 0: repository setup complete)")

    # For now, just show that we've initialized
    print("✓ Chess Analyser initialized successfully")
    print("✓ Phase 0 (Repository Setup) complete")


if __name__ == "__main__":
    main()
