"""Fixture tests for Chess.com board-side and clock signals."""

from pathlib import Path

import cv2
import pytest

from chess_analyser.detection import (
	BoardDetector,
	ChessComClockDetector,
	OccupancyDetector,
	OrientationDetector,
	SquareDetector,
	TemplatePieceDetector,
)


SESSION = Path("assets/training_sessions/20260813_111916_chesscom_green_session")
BLACK_SESSION = Path("assets/training_sessions/20260813_115622_black_game")


@pytest.mark.standard_screen
@pytest.mark.parametrize(
	("frame_name", "expected_side"),
	[("frame_000002.png", "bottom"), ("frame_000003.png", "top")],
)
def test_recorded_game_clock_identifies_active_board_side(frame_name: str, expected_side: str):
	image = cv2.imread(str(SESSION / frame_name))
	if image is None:
		pytest.skip("Recorded game fixture is not available")
	board = BoardDetector(min_confidence=0.55).detect(image)
	assert board is not None

	result = ChessComClockDetector().detect(image, board)

	assert result.side == expected_side
	assert result.confidence >= 0.5


@pytest.mark.standard_screen
def test_black_game_fixture_detects_black_bottom_and_maps_turn():
	image = cv2.imread(str(BLACK_SESSION / "frame_000002.png"))
	if image is None:
		pytest.skip("Black-game screenshot fixture is not available")
	board = BoardDetector(min_confidence=0.50).detect(image)
	assert board is not None

	# Start with the normal mapping only to collect screen-space color evidence.
	provisional = type(board)(board.x, board.y, board.width, board.height, board.square_size, board.confidence, "white_bottom")
	squares = SquareDetector().map_squares(provisional)
	occupancy = OccupancyDetector().detect(image, squares)
	pieces = TemplatePieceDetector("assets/piece_templates").detect(image, squares, occupancy)
	corner_names = {"top_left": "a8", "top_right": "h8", "bottom_left": "a1", "bottom_right": "h1"}
	evidence = {
		corner: pieces[name].piece
		for corner, name in corner_names.items()
		if name in pieces and pieces[name].piece != "unknown"
	}
	orientation = OrientationDetector().detect(corner_pieces=evidence)
	clock = ChessComClockDetector().detect(image, board)

	assert orientation.orientation == "black_bottom"
	assert orientation.confidence >= 0.65
	assert clock.side == "top"
	# The top clock belongs to White when Black is displayed at the bottom.
	player_at_bottom = "black" if orientation.orientation == "black_bottom" else "white"
	active_player = player_at_bottom if clock.side == "bottom" else ("black" if player_at_bottom == "white" else "white")
	assert active_player == "white"