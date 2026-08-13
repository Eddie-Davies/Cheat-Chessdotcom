"""Phase 10 position reconstruction tests."""

from pathlib import Path

import cv2
import pytest

from chess_analyser.chess import (
	LowConfidencePositionError,
	PositionReconstructionError,
	PositionReconstructor,
)
from chess_analyser.detection import (
	BoardDetection,
	OccupancyDetector,
	PieceDetection,
	SquareDetector,
	TemplatePieceDetector,
)


FIXTURE = Path("assets/test_screens/chesscom_standard_start/source.png")
TEMPLATES = Path("assets/piece_templates")
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_known_piece_map_reconstructs_fen_and_confidence():
	reconstructor = PositionReconstructor(confidence_threshold=0.8)
	result = reconstructor.reconstruct(
		{
			"e1": PieceDetection("e1", "white_king", 0.95),
			"e8": PieceDetection("e8", "black_king", 0.94),
			"e2": PieceDetection("e2", "white_pawn", 0.9),
			"d7": PieceDetection("d7", "black_pawn", 0.88),
		},
		side_to_move="black",
	)

	assert result.fen == "4k3/3p4/8/8/8/8/4P3/4K3 b - - 0 1"
	assert result.position.is_valid()
	assert result.confidence == pytest.approx(0.88)
	assert result.stable


@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_uploaded_starting_position_reconstructs_correct_fen():
	image = cv2.imread(str(FIXTURE))
	board = BoardDetection(247, 152, 928, 928, 116, 0.86, "white_bottom")
	squares = SquareDetector().map_squares(board)
	occupancy = OccupancyDetector().detect(image, squares)
	pieces = TemplatePieceDetector(TEMPLATES).detect(image, squares, occupancy)

	result = PositionReconstructor(confidence_threshold=0.55).reconstruct(
		pieces,
		occupancy=occupancy,
		side_to_move="white",
		castling_rights="KQkq",
	)

	assert result.fen == STARTING_FEN
	assert result.confidence >= 0.55
	assert result.pieces["a8"] == "black_rook"
	assert result.pieces["e1"] == "white_king"


def test_orientation_corrected_square_mapping_can_reconstruct_flipped_board():
	board = BoardDetection(100, 50, 800, 800, 100, 0.9, "black_bottom")
	squares = SquareDetector().map_squares(board)
	# The mapper's algebraic keys are already corrected from screen positions.
	assert squares["h1"].x == 100
	assert squares["a8"].x == 800

	result = PositionReconstructor().reconstruct(
		{
			"h1": "white_king",
			"a8": "black_king",
		},
		side_to_move="white",
	)

	assert result.fen.startswith("k7/8/8/8/8/8/8/7K w - -")


def test_missing_kings_are_rejected():
	with pytest.raises(PositionReconstructionError, match="white king"):
		PositionReconstructor().reconstruct(
			{"e8": "black_king", "e2": "white_pawn"}, side_to_move="white"
		)


def test_invalid_piece_and_low_confidence_are_rejected():
	with pytest.raises(PositionReconstructionError, match="Unknown piece"):
		PositionReconstructor().reconstruct(
			{"e1": "white_king", "e8": "black_king", "e2": "dragon"}, side_to_move="white"
		)
	with pytest.raises(LowConfidencePositionError, match="Low-confidence piece"):
		PositionReconstructor(confidence_threshold=0.8).reconstruct(
			{
				"e1": PieceDetection("e1", "white_king", 0.9),
				"e8": PieceDetection("e8", "black_king", 0.9),
				"e2": PieceDetection("e2", "white_pawn", 0.4),
			},
			side_to_move="white",
		)


def test_invalid_position_and_occupancy_mismatch_are_rejected():
	with pytest.raises(PositionReconstructionError, match="Invalid chess position"):
		PositionReconstructor().reconstruct(
			{"e1": "white_king", "e8": "black_king", "a1": "white_pawn"},
			side_to_move="white",
			castling_rights="K",
		)
	with pytest.raises(PositionReconstructionError, match="not marked occupied"):
		PositionReconstructor().reconstruct(
			{"e1": "white_king", "e8": "black_king"},
			side_to_move="white",
			occupancy={"e1": type("Occupancy", (), {"status": "empty", "confidence": 1.0})()},
		)