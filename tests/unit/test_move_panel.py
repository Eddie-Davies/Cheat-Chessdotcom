"""Tests for the side-docked move-instruction panel's pure logic."""

from chess_analyser.overlay import MovePanel, describe_move


def test_describe_move_names_piece_and_squares():
	pieces = {"g1": "white_knight"}

	instruction = describe_move(pieces, "g1f3")

	assert instruction == "Move white knight from g1 to f3"


def test_describe_move_handles_promotion():
	pieces = {"a7": "white_pawn"}

	instruction = describe_move(pieces, "a7a8q")

	assert instruction == "Move white pawn from a7 to a8, promoting to queen"


def test_describe_move_falls_back_without_piece_data():
	instruction = describe_move(None, "e2e4")

	assert instruction == "Move piece from e2 to e4"


def test_describe_move_rejects_invalid_uci_gracefully():
	instruction = describe_move({}, "not-a-move")

	assert instruction == "Play not-a-move"


def test_move_panel_is_importable_for_manual_diagnostics():
	assert callable(MovePanel)
