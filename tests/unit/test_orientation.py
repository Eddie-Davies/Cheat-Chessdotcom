"""Unit tests for Phase 7 board orientation detection."""

from chess_analyser.detection import OrientationDetector


def test_normal_orientation_from_board_labels():
    result = OrientationDetector().detect(labels={"bottom": "1", "left": "a"})

    assert result.orientation == "white_bottom"
    assert result.confidence > 0.8
    assert len(result.signals) == 2


def test_flipped_orientation_from_board_labels():
    result = OrientationDetector().detect(labels={"bottom": "8", "left": "h"})

    assert result.orientation == "black_bottom"
    assert result.confidence > 0.8


def test_piece_and_history_signals_can_confirm_normal_orientation():
    result = OrientationDetector().detect(
        corner_pieces={"top_left": "black_rook", "bottom_left": "white_rook"},
        orientation_history=["unknown", "white_bottom"],
    )

    assert result.orientation == "white_bottom"
    assert result.confidence > 0.8
    assert any(signal.startswith("piece:") for signal in result.signals)
    assert "history:white_bottom" in result.signals


def test_piece_evidence_can_confirm_flipped_orientation():
    result = OrientationDetector().detect(
        corner_pieces={"top_left": "white_rook", "bottom_left": "black_rook"}
    )

    assert result.orientation == "black_bottom"
    assert result.confidence > 0.7


def test_screen_space_piece_colors_support_black_bottom_games():
    result = OrientationDetector().detect(
        corner_pieces={"top_left": "white_rook", "bottom_left": "black_rook"}
    )

    assert result.orientation == "black_bottom"
    assert result.confidence > 0.7


def test_conflicting_signals_return_unknown():
    result = OrientationDetector().detect(
        labels={"bottom": "1"},
        corner_pieces={"bottom_left": "black_rook"},
    )

    assert result.orientation == "unknown"
    assert result.confidence == 0.5
    assert result.signals


def test_missing_evidence_returns_unknown_with_zero_confidence():
    result = OrientationDetector().detect()

    assert result.orientation == "unknown"
    assert result.confidence == 0.0
    assert result.signals == ()


def test_invalid_history_does_not_create_a_guess():
    result = OrientationDetector().detect(orientation_history=["unknown", "not_known"])

    assert result.orientation == "unknown"
    assert result.confidence == 0.0