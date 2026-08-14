"""Fixture tests for Lichess active-clock detection."""

from pathlib import Path

import cv2
import pytest

from chess_analyser.detection import BoardDetector
from chess_analyser.detection.lichess_ui import LichessClockDetector


SESSION = Path("assets/LiChess")


@pytest.mark.parametrize(
	"frame_name",
	["Screenshot 2026-08-14 123859.png", "Screenshot 2026-08-14 124018.png"],
)
def test_own_turn_screenshots_identify_the_bottom_clock_as_active(frame_name: str):
	image = cv2.imread(str(SESSION / frame_name))
	if image is None:
		pytest.skip("Lichess turn fixture is not available")
	board = BoardDetector(min_confidence=0.5).detect(image)
	assert board is not None

	result = LichessClockDetector().detect(image, board)

	assert result.side == "bottom"
	assert result.confidence >= 0.5
