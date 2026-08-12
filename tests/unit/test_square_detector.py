"""Unit tests for Phase 6 square mapping."""

from pathlib import Path

import cv2
import numpy as np

from chess_analyser.detection import BoardDetection, SquareDetector


def make_board(orientation: str = "white_bottom") -> BoardDetection:
    return BoardDetection(
        x=137,
        y=83,
        width=333,
        height=319,
        square_size=333 / 8,
        confidence=0.9,
        orientation=orientation,
    )


def test_all_64_squares_exist_and_are_unique():
    squares = SquareDetector().map_squares(make_board())

    assert len(squares) == 64
    assert set(squares) == {f"{file}{rank}" for file in "abcdefgh" for rank in range(1, 9)}
    assert len({square.square for square in squares.values()}) == 64


def test_normal_orientation_maps_screen_corners_correctly():
    squares = SquareDetector().map_squares(make_board("white_bottom"))

    assert squares["a8"].x == 137
    assert squares["a8"].y == 83
    assert squares["h1"].pixel_bounds == (round(137 + 7 * 333 / 8), round(83 + 7 * 319 / 8), 470, 402)
    assert squares["a1"].center == (
        137 + (333 / 8) / 2,
        83 + 7 * (319 / 8) + (319 / 8) / 2,
    )


def test_flipped_orientation_maps_screen_corners_correctly():
    squares = SquareDetector().map_squares(make_board("black_bottom"))

    assert squares["h1"].x == 137
    assert squares["h1"].y == 83
    assert squares["a8"].pixel_bounds == (round(137 + 7 * 333 / 8), round(83 + 7 * 319 / 8), 470, 402)
    assert squares["a1"].center == (
        137 + 7 * (333 / 8) + (333 / 8) / 2,
        83 + (319 / 8) / 2,
    )


def test_square_boundaries_tile_board_without_overlap_or_gaps():
    board = make_board()
    squares = SquareDetector().map_squares(board)
    for row in range(8):
        row_squares = [squares[f"{file}{8 - row}"].pixel_bounds for file in "abcdefgh"]
        assert row_squares[0][0] == round(board.x)
        assert row_squares[-1][2] == round(board.x + board.width)
        for previous, current in zip(row_squares, row_squares[1:]):
            assert previous[2] == current[0]
            assert previous[1] == current[1]
            assert previous[3] == current[3]
    for file in "abcdefgh":
        column_squares = [squares[f"{file}{rank}"].pixel_bounds for rank in range(1, 9)]
        column_squares.sort(key=lambda bounds: bounds[1])
        assert column_squares[0][1] == round(board.y)
        assert column_squares[-1][3] == round(board.y + board.height)
        for previous, current in zip(column_squares, column_squares[1:]):
            assert previous[3] == current[1]
            assert previous[0] == current[0]
            assert previous[2] == current[2]
    assert min(square.x for square in squares.values()) == board.x
    assert min(square.y for square in squares.values()) == board.y
    assert max(square.x + square.width for square in squares.values()) == board.x + board.width
    assert max(square.y + square.height for square in squares.values()) == board.y + board.height


def test_unknown_orientation_uses_normal_mapping():
    squares = SquareDetector().map_squares(make_board("unknown"))

    assert squares["a8"].center == SquareDetector().map_squares(make_board("white_bottom"))["a8"].center


def test_label_diagnostic_renders_output(tmp_path: Path):
    image = np.zeros((500, 600, 3), dtype=np.uint8)
    output = SquareDetector().render_labels(image, make_board(), tmp_path / "labels.png")

    rendered = cv2.imread(str(output))
    assert rendered is not None
    assert rendered.shape == image.shape
    assert np.count_nonzero(rendered) > 0