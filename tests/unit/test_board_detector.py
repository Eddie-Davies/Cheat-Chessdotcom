"""Unit and fixture-style tests for automatic board detection."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from chess_analyser.detection import BoardDetector


def make_board_fixture(
    *,
    board_x: int = 137,
    board_y: int = 83,
    board_size: int = 320,
    light: tuple[int, int, int] = (210, 190, 160),
    dark: tuple[int, int, int] = (95, 125, 155),
) -> np.ndarray:
    """Create a board embedded in a nonuniform desktop-like background."""
    image = np.zeros((560, 760, 3), dtype=np.uint8)
    image[:] = (34, 38, 44)
    cv2.rectangle(image, (30, 30), (730, 530), (48, 52, 60), 2)
    square_size = board_size // 8
    cv2.rectangle(
        image,
        (board_x - 5, board_y - 5),
        (board_x + board_size + 4, board_y + board_size + 4),
        (10, 10, 10),
        -1,
    )
    for row in range(8):
        for column in range(8):
            color = light if (row + column) % 2 == 0 else dark
            top_left = (board_x + column * square_size, board_y + row * square_size)
            bottom_right = (top_left[0] + square_size - 1, top_left[1] + square_size - 1)
            cv2.rectangle(image, top_left, bottom_right, color, -1)
    return image


def test_detects_light_board_geometry_and_confidence():
    image = make_board_fixture()
    detector = BoardDetector(min_confidence=0.55)

    result = detector.detect(image)

    assert result is not None
    assert abs(result.x - 132) <= 8
    assert abs(result.y - 78) <= 8
    assert abs(result.width - 330) <= 16
    assert abs(result.height - 330) <= 16
    assert result.square_size == pytest.approx(result.width / 8, abs=2)
    assert 0.55 <= result.confidence <= 1.0
    assert result.orientation == "unknown"


def test_detects_dark_board_theme_without_colour_assumption():
    image = make_board_fixture(
        board_x=241,
        board_y=149,
        board_size=280,
        light=(55, 85, 105),
        dark=(18, 28, 38),
    )
    detector = BoardDetector(min_confidence=0.55)

    result = detector.detect(image)

    assert result is not None
    assert abs(result.x - 236) <= 8
    assert abs(result.y - 144) <= 8
    assert abs(result.width - 290) <= 12
    assert result.confidence >= 0.55


def test_real_desktop_capture_without_board_is_rejected():
    fixture_path = Path("assets/test_screens/capture_phase4.png")
    if not fixture_path.exists():
        pytest.skip("Phase 4 desktop capture fixture is not available")
    image = cv2.imread(str(fixture_path))
    assert image is not None

    result = BoardDetector().detect(image)

    assert result is None


def test_real_chess_com_fixture_detects_board_scale_and_bounds():
    fixture_path = Path("assets/test_screens/chess_com_board_01.png")
    if not fixture_path.exists():
        pytest.skip("Uploaded Chess.com fixture is not available")
    image = cv2.imread(str(fixture_path))
    assert image is not None

    result = BoardDetector().detect(image)

    assert result is not None
    assert 240 <= result.x <= 255
    assert 145 <= result.y <= 160
    assert 900 <= result.width <= 950
    assert 900 <= result.height <= 950
    assert result.square_size == pytest.approx(116, abs=3)
    assert result.confidence >= 0.75


def test_diagnostic_draw_saves_box_and_grid(tmp_path: Path):
    image = make_board_fixture()
    detector = BoardDetector(min_confidence=0.55)
    result = detector.detect(image)
    assert result is not None

    output = detector.draw_diagnostic(image, result, tmp_path / "detected.png")

    diagnostic = cv2.imread(str(output))
    assert diagnostic is not None
    assert diagnostic.shape == image.shape
    assert not np.array_equal(diagnostic, image)


def test_invalid_images_are_rejected():
    detector = BoardDetector()

    with pytest.raises(TypeError):
        detector.detect("not an image")
    with pytest.raises(ValueError):
        detector.detect(np.zeros((20, 20), dtype=np.uint8))