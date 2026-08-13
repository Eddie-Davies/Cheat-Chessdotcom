"""Tests for Phase 8 empty/occupied square detection."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from chess_analyser.detection import BoardDetection, OccupancyDetector, SquareDetector


def make_board_fixture() -> tuple[np.ndarray, dict]:
    board = BoardDetection(40, 30, 320, 320, 40, 0.9, "white_bottom")
    image = np.zeros((400, 460, 3), dtype=np.uint8)
    squares = SquareDetector().map_squares(board)
    for index, square in enumerate(squares.values()):
        color = (205, 185, 150) if index % 2 == 0 else (95, 125, 155)
        left, top, right, bottom = square.pixel_bounds
        image[top:bottom, left:right] = color
    for name in ("a1", "e4", "h8"):
        square = squares[name]
        center = tuple(round(value) for value in square.center)
        cv2.circle(image, center, 13, (35, 35, 35), -1)
    return image, squares


def test_detects_empty_and_occupied_squares_without_piece_classification():
    image, squares = make_board_fixture()
    results = OccupancyDetector().detect(image, squares)

    assert set(results) == set(squares)
    assert results["a1"].status == "occupied"
    assert results["e4"].status == "occupied"
    assert results["h8"].status == "occupied"
    assert results["d4"].status == "empty"
    assert results["d4"].confidence > 0.5
    assert results["a1"].foreground_ratio > results["d4"].foreground_ratio


def test_uncertain_result_is_available_for_ambiguous_activity():
    board = BoardDetection(0, 0, 640, 640, 80, 0.9, "white_bottom")
    squares = SquareDetector().map_squares(board)
    image = np.full((640, 640, 3), 128, dtype=np.uint8)
    square = squares["a8"]
    left, top, right, bottom = square.pixel_bounds
    image[top:bottom, left:right] = 128
    cv2.rectangle(image, (left + 15, top + 20), (left + 25, bottom - 20), (180, 180, 180), -1)

    result = OccupancyDetector().detect(image, {"a8": square})["a8"]

    assert result.status == "uncertain"
    assert 0 < result.confidence < 1


def test_real_chess_com_fixture_finds_many_occupied_and_empty_squares():
    fixture_path = Path("assets/test_screens/chesscom_standard_start/source.png")
    if not fixture_path.exists():
        pytest.skip("Uploaded Chess.com fixture is not available")
    image = cv2.imread(str(fixture_path))
    assert image is not None
    board = BoardDetection(247, 152, 928, 928, 116, 0.86, "white_bottom")
    squares = SquareDetector().map_squares(board)

    results = OccupancyDetector().detect(image, squares)

    occupied = [result for result in results.values() if result.status == "occupied"]
    empty = [result for result in results.values() if result.status == "empty"]
    assert len(occupied) >= 24
    assert len(empty) >= 20


def test_diagnostic_rendering_writes_output(tmp_path: Path):
    image, squares = make_board_fixture()
    detector = OccupancyDetector()
    results = detector.detect(image, squares)

    output = detector.render_diagnostic(image, squares, results, tmp_path / "occupancy.png")

    rendered = cv2.imread(str(output))
    assert rendered is not None
    assert rendered.shape == image.shape
    assert np.count_nonzero(rendered != image) > 0