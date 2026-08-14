"""Representative dataset tests for Phase 9 template recognition."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from chess_analyser.detection import (
	BoardDetection,
	BoardDetector,
	OccupancyDetector,
	SquareDetector,
	TemplatePieceDetector,
)


FIXTURE = Path("assets/test_screens/chesscom_standard_start/source.png")
BLACK_START_FIXTURE = Path("assets/Screenshot 2026-08-13 121802.png")
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
@pytest.mark.skipif(not BLACK_START_FIXTURE.exists(), reason="Black-bottom screenshot is not available")
def test_black_bottom_starting_fixture_recognizes_all_32_pieces():
	image = cv2.imread(str(BLACK_START_FIXTURE))
	detected_board = BoardDetector(min_confidence=0.50).detect(image)
	assert detected_board is not None
	board = BoardDetection(
		detected_board.x,
		detected_board.y,
		detected_board.width,
		detected_board.height,
		detected_board.square_size,
		detected_board.confidence,
		"black_bottom",
	)
	squares = SquareDetector().map_squares(board)
	occupancy = OccupancyDetector().detect(image, squares)
	results = TemplatePieceDetector(TEMPLATES).detect(image, squares, occupancy)

	assert sum(value.status == "occupied" for value in occupancy.values()) == 32
	assert len(results) == 32
	assert all(result.confidence >= 0.65 for result in results.values())


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


def test_multiple_samples_per_piece_class_are_loaded(tmp_path: Path):
	for color in ("white", "black"):
		for piece in ("pawn", "knight", "bishop", "rook", "queen", "king"):
			directory = tmp_path / color
			directory.mkdir(parents=True, exist_ok=True)
			(source := TEMPLATES / color / f"{piece}.png").resolve()
			(directory / f"{piece}.png").write_bytes(source.read_bytes())
			(directory / f"{piece}_green_01.png").write_bytes(source.read_bytes())

	detector = TemplatePieceDetector(tmp_path)

	assert len(detector.templates) == 24


def test_template_features_ignore_alternate_square_backgrounds():
	image, _board, squares, _occupancy = fixture_data()
	square = squares["e2"]
	left, top, right, bottom = square.pixel_bounds
	patch = image[top:bottom, left:right].copy()
	alternate = patch.copy()
	background = alternate[0, 0].copy()
	foreground = cv2.cvtColor(alternate, cv2.COLOR_BGR2LAB)
	background_mask = np.linalg.norm(foreground - foreground[0, 0], axis=2) < 12
	alternate[background_mask] = (20, 180, 40)

	original = TemplatePieceDetector._extract_features_from_image("original", patch)
	changed = TemplatePieceDetector._extract_features_from_image("changed", alternate)

	assert original.contour is not None
	assert changed.contour is not None
	assert TemplatePieceDetector._score(original, changed) >= 0.65


def test_template_features_include_scale_normalized_negative_space():
	image, _board, squares, _occupancy = fixture_data()
	left, top, right, bottom = squares["e2"].pixel_bounds
	features = TemplatePieceDetector._extract_features_from_image("pawn", image[top:bottom, left:right])

	assert features.negative_space.shape == (24, 24)
	assert 0.0 <= float(features.negative_space.min()) <= 1.0
	assert 0.0 <= float(features.negative_space.max()) <= 1.0