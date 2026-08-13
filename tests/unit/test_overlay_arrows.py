"""Phase 15 move-arrow geometry tests."""

import pytest

from chess_analyser.detection import BoardDetection
from chess_analyser.overlay import ArrowRenderer


def board(orientation="white_bottom"):
	return BoardDetection(100, 50, 800, 640, 100, 0.9, orientation)


def test_e2_e4_geometry_on_normal_board():
	geometry = ArrowRenderer().geometry(board(), "e2e4")

	assert geometry.source_square == "e2"
	assert geometry.destination_square == "e4"
	assert geometry.start == (550.0, 570.0)
	assert geometry.end == (550.0, 410.0)


def test_flipped_board_reverses_screen_coordinates():
	geometry = ArrowRenderer().geometry(board("black_bottom"), "e2e4")

	assert geometry.start == (450.0, 170.0)
	assert geometry.end == (450.0, 330.0)


def test_capture_and_promotion_use_correct_source_and_destination():
	renderer = ArrowRenderer()

	capture = renderer.geometry(board(), "d5e6")
	promotion = renderer.geometry(board(), "a7a8q")

	assert (capture.source_square, capture.destination_square) == ("d5", "e6")
	assert (promotion.source_square, promotion.destination_square) == ("a7", "a8")
	assert promotion.start == (150.0, 170.0)
	assert promotion.end == (150.0, 90.0)


def test_invalid_uci_move_is_rejected():
	with pytest.raises(ValueError, match="Invalid UCI move"):
		ArrowRenderer().geometry(board(), "not-a-move")


class FakeCanvas:
	def __init__(self):
		self.lines = []

	def create_line(self, *args, **kwargs):
		self.lines.append((args, kwargs))


def test_draw_on_canvas_uses_board_local_coordinates():
	canvas = FakeCanvas()
	geometry = ArrowRenderer().draw_on_canvas(canvas, board(), "e2e4")

	assert len(canvas.lines) == 1
	args, kwargs = canvas.lines[0]
	assert args == (450.0, 520.0, 450.0, 360.0)
	assert kwargs["arrow"] == "last"
	assert kwargs["tags"] == "move-arrow"
	assert geometry.destination_square == "e4"