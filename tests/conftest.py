"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Real screenshot regression tests target the green Chess.com board theme.
GREEN_SCREEN_FIXTURES = project_root / "assets" / "test_screens"
GREEN_BOARD_FIXTURE_DIRS = (
	GREEN_SCREEN_FIXTURES / "chesscom_standard_start",
	GREEN_SCREEN_FIXTURES / "chesscom_green_active_game",
)
