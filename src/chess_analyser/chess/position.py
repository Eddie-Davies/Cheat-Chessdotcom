"""Position model and history management backed by ``python-chess``."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field

import chess as chess_lib

from .fen import board_from_fen, board_to_fen
from .moves import legal_uci_moves, san_from_uci, uci_from_san


class PositionValidationError(ValueError):
	"""Raised when a chess position is not valid according to python-chess."""


PieceData = Mapping[str, str | chess_lib.Piece]
PositionKey = tuple[str, bool, str, str | None]


_PIECE_NAMES = {
	"white_pawn": "P",
	"white_knight": "N",
	"white_bishop": "B",
	"white_rook": "R",
	"white_queen": "Q",
	"white_king": "K",
	"black_pawn": "p",
	"black_knight": "n",
	"black_bishop": "b",
	"black_rook": "r",
	"black_queen": "q",
	"black_king": "k",
}


@dataclass
class ChessPosition:
	"""A chess position with stable identity and position history."""

	board: chess_lib.Board
	_history: list[PositionKey] = field(default_factory=list, repr=False)

	def __post_init__(self) -> None:
		if not self._history:
			self._history.append(self.position_key())

	@classmethod
	def starting(cls) -> "ChessPosition":
		"""Create the standard starting position."""
		return cls(chess_lib.Board())

	@classmethod
	def from_fen(cls, fen: str) -> "ChessPosition":
		"""Create a position from a full FEN string."""
		return cls(board_from_fen(fen))

	@classmethod
	def from_pieces(
		cls,
		pieces: PieceData,
		*,
		side_to_move: chess_lib.Color = chess_lib.WHITE,
		castling_rights: str = "-",
		en_passant: str | None = None,
		halfmove_clock: int = 0,
		fullmove_number: int = 1,
	) -> "ChessPosition":
		"""Create a position from algebraic squares and piece values."""
		board = chess_lib.Board(None)
		board.turn = side_to_move
		board.halfmove_clock = halfmove_clock
		board.fullmove_number = fullmove_number
		try:
			board.set_castling_fen(castling_rights)
			board.ep_square = chess_lib.parse_square(en_passant) if en_passant else None
			for square, piece_value in pieces.items():
				board.set_piece_at(chess_lib.parse_square(square), _parse_piece(piece_value))
		except (TypeError, ValueError) as exc:
			raise PositionValidationError(f"Invalid piece data: {exc}") from exc
		return cls(board)

	@property
	def fen(self) -> str:
		"""Return the complete FEN, including clocks."""
		return board_to_fen(self.board)

	@property
	def history(self) -> tuple[PositionKey, ...]:
		"""Return immutable position keys in observation order."""
		return tuple(self._history)

	def position_key(self) -> PositionKey:
		"""Return the stable identity used for equality and change tracking."""
		return (
			self.board.board_fen(),
			self.board.turn,
			self.board.castling_xfen(),
			chess_lib.square_name(self.board.ep_square) if self.board.ep_square is not None else None,
		)

	def position_hash(self) -> str:
		"""Return a deterministic SHA-256 hash of the position key."""
		return hashlib.sha256(repr(self.position_key()).encode("utf-8")).hexdigest()

	def record(self) -> PositionKey:
		"""Record the current position and return its key."""
		key = self.position_key()
		self._history.append(key)
		return key

	def has_changed(self, other: "ChessPosition") -> bool:
		"""Return whether the board state differs from another position."""
		return self.position_key() != other.position_key()

	def is_valid(self) -> bool:
		"""Return whether python-chess considers the position valid."""
		return self.board.is_valid()

	def validate(self) -> None:
		"""Raise ``PositionValidationError`` when the position is invalid."""
		if not self.is_valid():
			status = self.board.status()
			raise PositionValidationError(f"Invalid chess position (status={status})")

	def legal_moves(self) -> list[str]:
		"""Return all legal moves in UCI notation."""
		return legal_uci_moves(self.board)

	def uci_to_san(self, uci_move: str) -> str:
		"""Convert a legal UCI move to SAN."""
		return san_from_uci(self.board, uci_move)

	def san_to_uci(self, san_move: str) -> str:
		"""Convert a legal SAN move to UCI."""
		return uci_from_san(self.board, san_move)

	def push_uci(self, uci_move: str) -> PositionKey:
		"""Apply a legal UCI move and record the resulting position."""
		try:
			move = chess_lib.Move.from_uci(uci_move)
		except ValueError as exc:
			raise ValueError(f"Invalid UCI move: {uci_move}") from exc
		if move not in self.board.legal_moves:
			raise ValueError(f"Illegal UCI move: {uci_move}")
		self.board.push(move)
		return self.record()

	def push_san(self, san_move: str) -> PositionKey:
		"""Apply a legal SAN move and record the resulting position."""
		try:
			move = self.board.parse_san(san_move)
		except ValueError as exc:
			raise ValueError(f"Invalid or illegal SAN move: {san_move}") from exc
		self.board.push(move)
		return self.record()

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, ChessPosition):
			return NotImplemented
		return self.position_key() == other.position_key()


def _parse_piece(piece_value: str | chess_lib.Piece) -> chess_lib.Piece:
	if isinstance(piece_value, chess_lib.Piece):
		return piece_value
	symbol = _PIECE_NAMES.get(piece_value, piece_value)
	if not isinstance(symbol, str) or len(symbol) != 1 or symbol not in "PNBRQKpnbrqk":
		raise ValueError(f"Unknown piece value: {piece_value!r}")
	return chess_lib.Piece.from_symbol(symbol)
