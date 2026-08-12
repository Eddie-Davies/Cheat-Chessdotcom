"""Move conversion and legal-move helpers."""

from __future__ import annotations

import chess


def legal_uci_moves(board: chess.Board) -> list[str]:
	"""Return legal moves in deterministic UCI order."""
	return sorted(move.uci() for move in board.legal_moves)


def san_from_uci(board: chess.Board, uci_move: str) -> str:
	"""Convert a legal UCI move to SAN."""
	try:
		move = chess.Move.from_uci(uci_move)
	except ValueError as exc:
		raise ValueError(f"Invalid UCI move: {uci_move}") from exc
	if move not in board.legal_moves:
		raise ValueError(f"Illegal UCI move: {uci_move}")
	return board.san(move)


def uci_from_san(board: chess.Board, san_move: str) -> str:
	"""Convert a legal SAN move to UCI."""
	try:
		return board.parse_san(san_move).uci()
	except ValueError as exc:
		raise ValueError(f"Invalid or illegal SAN move: {san_move}") from exc
