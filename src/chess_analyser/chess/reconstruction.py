"""Reconstruct validated chess positions from visual piece detections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import chess

from chess_analyser.detection.piece_detector import OccupancyDetection, PieceDetection

from .position import ChessPosition, PositionValidationError


class PositionReconstructionError(ValueError):
	"""Raised when visual detections cannot form a valid chess position."""


class LowConfidencePositionError(PositionReconstructionError):
	"""Raised when a position is not reliable enough for downstream analysis."""


@dataclass(frozen=True)
class PositionDetection:
	"""Validated reconstructed position and its visual confidence."""

	pieces: dict[str, str]
	side_to_move: str
	fen: str
	confidence: float
	stable: bool
	position: ChessPosition = field(repr=False, compare=False)


class PositionReconstructor:
	"""Connect orientation-corrected piece detections to ``ChessPosition``."""

	_VALID_PIECES = {
		"white_pawn",
		"white_knight",
		"white_bishop",
		"white_rook",
		"white_queen",
		"white_king",
		"black_pawn",
		"black_knight",
		"black_bishop",
		"black_rook",
		"black_queen",
		"black_king",
	}

	def __init__(self, *, confidence_threshold: float = 0.55) -> None:
		if not 0 <= confidence_threshold <= 1:
			raise ValueError("confidence_threshold must be between 0 and 1")
		self.confidence_threshold = confidence_threshold

	def reconstruct(
		self,
		piece_detections: Mapping[str, PieceDetection | str],
		*,
		occupancy: Mapping[str, OccupancyDetection] | None = None,
		side_to_move: str = "white",
		castling_rights: str = "-",
		en_passant: str | None = None,
		halfmove_clock: int = 0,
		fullmove_number: int = 1,
	) -> PositionDetection:
		"""Build and validate a position from algebraic, orientation-corrected detections."""
		if side_to_move not in {"white", "black"}:
			raise PositionReconstructionError("side_to_move must be 'white' or 'black'")
		if not piece_detections:
			raise PositionReconstructionError("No piece detections were supplied")

		pieces: dict[str, str] = {}
		confidences: list[float] = []
		for square, detection in piece_detections.items():
			if square not in _VALID_SQUARES:
				raise PositionReconstructionError(f"Invalid algebraic square: {square}")
			piece, confidence = self._piece_value(detection)
			if piece not in self._VALID_PIECES:
				raise PositionReconstructionError(f"Unknown piece classification at {square}: {piece}")
			if confidence < self.confidence_threshold:
				raise LowConfidencePositionError(
					f"Low-confidence piece at {square}: {confidence:.3f} < {self.confidence_threshold:.3f}"
				)
			if occupancy is not None:
				occupancy_result = occupancy.get(square)
				if occupancy_result is None or occupancy_result.status != "occupied":
					raise PositionReconstructionError(f"Piece at {square} is not marked occupied")
				if occupancy_result.confidence < self.confidence_threshold:
					raise LowConfidencePositionError(f"Low-confidence occupancy at {square}")
				confidences.append(occupancy_result.confidence)
			pieces[square] = piece
			confidences.append(confidence)

		self._require_kings(pieces)
		try:
			position = ChessPosition.from_pieces(
				pieces,
				side_to_move=chess.WHITE if side_to_move == "white" else chess.BLACK,
				castling_rights=castling_rights,
				en_passant=en_passant,
				halfmove_clock=halfmove_clock,
				fullmove_number=fullmove_number,
			)
			position.validate()
		except (PositionValidationError, ValueError) as exc:
			raise PositionReconstructionError(str(exc)) from exc

		confidence = min(confidences) if confidences else 0.0
		return PositionDetection(pieces, side_to_move, position.fen, confidence, True, position)

	@staticmethod
	def _piece_value(detection: PieceDetection | str) -> tuple[str, float]:
		if isinstance(detection, PieceDetection):
			return detection.piece, detection.confidence
		return detection, 1.0

	@staticmethod
	def _require_kings(pieces: Mapping[str, str]) -> None:
		if sum(piece == "white_king" for piece in pieces.values()) != 1:
			raise PositionReconstructionError("Position must contain exactly one white king")
		if sum(piece == "black_king" for piece in pieces.values()) != 1:
			raise PositionReconstructionError("Position must contain exactly one black king")


_VALID_SQUARES = {f"{file}{rank}" for file in "abcdefgh" for rank in range(1, 9)}