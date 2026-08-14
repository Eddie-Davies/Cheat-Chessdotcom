"""
Unit tests for application initialization and settings.
"""

import pytest

from chess_analyser import __version__
from chess_analyser.config import AppSettings, DEFAULT_SETTINGS
from chess_analyser.logging import get_logger, setup_logging


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_default_settings():
    """Test default settings configuration."""
    assert DEFAULT_SETTINGS.engine_depth == 20
    assert DEFAULT_SETTINGS.multipv == 5
    assert DEFAULT_SETTINGS.overlay_alpha == 0.8
    assert DEFAULT_SETTINGS.piece_confidence_threshold == 0.45


def test_settings_validation():
    """Test that invalid settings raise errors."""
    with pytest.raises(ValueError):
        AppSettings(piece_confidence_threshold=1.5)

    with pytest.raises(ValueError):
        AppSettings(board_confidence_threshold=-0.1)

    with pytest.raises(ValueError):
        AppSettings(overlay_alpha=2.0)


def test_logging_setup():
    """Test that logging can be configured."""
    logger = setup_logging()
    assert logger is not None
    assert logger.name == "chess_analyser"


def test_get_logger():
    """Test getting a module logger."""
    logger = get_logger("test_module")
    assert logger is not None
    assert "test_module" in logger.name
