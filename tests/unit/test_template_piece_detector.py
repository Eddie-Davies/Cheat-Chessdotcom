"""Representative dataset tests for Phase 9 template recognition."""

from pathlib import Path

import cv2
import pytest

from chess_analyser.detection import (
	BoardDetection,
	OccupancyDetector,
	SquareDetector,
	TemplatePieceDetector,
)


FIXTURE = Path("assets/test_screens/chesscom_standard_start/source.png")
TEMPLATES = Path("assets/piece_templates")


def fixture_data():
	image = cv2.imread(str(FIXTURE))
	board = BoardDetection(247, 152, 928, 928, 116, 0.86, "white_bottom")
	squares = SquareDetector().map_squares(board)
	occupancy = OccupancyDetector().detect(image, squares)
	return image, board, squares, occupancy


def starting_position_labels():
	return {
		**{f"{file}8": "black_" + piece for file, piece in zip("abcdefgh", ("rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"))},
		**{f"{file}7": "black_pawn" for file in "abcdefgh"},
		**{f"{file}2": "white_pawn" for file in "abcdefgh"},
		**{f"{file}1": "white_" + piece for file, piece in zip("abcdefgh", ("rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"))},
	}


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_recognizes_all_twelve_piece_classes():
	image, _board, squares, occupancy = fixture_data()
	detector = TemplatePieceDetector(TEMPLATES)
	results = detector.detect(image, squares, occupancy)
	expected = starting_position_labels()

	correct = {name for name, result in results.items() if result.piece == expected[name]}
	accuracy = len(correct) / len(expected)

	assert set(results) == set(expected)
	assert accuracy >= 0.90
	assert {result.piece for result in results.values()} == set(expected.values())
	assert all(0 <= result.confidence <= 1 for result in results.values())


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_template_matching_handles_scaled_board():
	image, board, _squares, _occupancy = fixture_data()
	scaled_image = cv2.resize(image, None, fx=0.75, fy=0.75, interpolation=cv2.INTER_AREA)
	scaled_board = BoardDetection(
		board.x * 0.75,
		board.y * 0.75,
		board.width * 0.75,
		board.height * 0.75,
		board.square_size * 0.75,
		board.confidence,
		board.orientation,
	)
	scaled_squares = SquareDetector().map_squares(scaled_board)
	occupancy = OccupancyDetector().detect(scaled_image, scaled_squares)
	results = TemplatePieceDetector(TEMPLATES).detect(scaled_image, scaled_squares, occupancy)
	expected = starting_position_labels()

	assert sum(result.piece == expected[name] for name, result in results.items()) >= 29


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_empty_squares_are_not_classified_when_occupancy_is_supplied():
	image, _board, squares, occupancy = fixture_data()
	results = TemplatePieceDetector(TEMPLATES).detect(image, squares, occupancy)

	assert "d4" not in results


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_piece_diagnostic_rendering(tmp_path: Path):
	image, _board, squares, occupancy = fixture_data()
	detector = TemplatePieceDetector(TEMPLATES)
	results = detector.detect(image, squares, occupancy)

	output = detector.render_diagnostic(image, squares, results, tmp_path / "pieces.png")

	annotated = cv2.imread(str(output))
	assert annotated is not None
	assert annotated.shape == image.shape


def test_missing_template_directory_is_rejected(tmp_path: Path):
	with pytest.raises(ValueError, match="No piece templates"):
		TemplatePieceDetector(tmp_path / "missing")