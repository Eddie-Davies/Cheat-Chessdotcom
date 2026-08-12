"""FEN parsing, generation, and validation helpers."""

from __future__ import annotations

import chess


def board_from_fen(fen: str) -> chess.Board:
	"""Parse a complete FEN and translate parser errors consistently."""
	try:
		return chess.Board(fen)
	except ValueError as exc:
		raise ValueError(f"Invalid FEN: {exc}") from exc


def board_to_fen(board: chess.Board) -> str:
	"""Generate a complete FEN from a board."""
	return board.fen(en_passant="fen")


def is_valid_fen(fen: str) -> bool:
	"""Return whether FEN parses and describes a valid position."""
	try:
		return board_from_fen(fen).is_valid()
	except ValueError:
		return False
