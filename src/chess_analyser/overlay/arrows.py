"""Pure move-arrow geometry and Tk canvas rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass

import chess

from chess_analyser.detection.board_detector import BoardDetection
from chess_analyser.detection.square_detector import SquareDetector


@dataclass(frozen=True)
class ArrowGeometry:
	"""Screen-space line geometry for a chess move arrow."""

	source_square: str
	destination_square: str
	start: tuple[float, float]
	end: tuple[float, float]


class ArrowRenderer:
	"""Convert UCI moves to board-relative arrow geometry and draw them."""

	def geometry(self, board: BoardDetection, uci_move: str) -> ArrowGeometry:
		"""Return source/destination centers for a valid UCI move."""
		try:
			move = chess.Move.from_uci(uci_move)
		except ValueError as exc:
			raise ValueError(f"Invalid UCI move: {uci_move}") from exc
		mapping = SquareDetector().map_squares(board)
		source_square = chess.square_name(move.from_square)
		destination_square = chess.square_name(move.to_square)
		return ArrowGeometry(
			source_square=source_square,
			destination_square=destination_square,
			start=mapping[source_square].center,
			end=mapping[destination_square].center,
		)

	def draw_on_canvas(
		self,
		canvas,
		board: BoardDetection,
		uci_move: str,
		*,
		color: str = "#ffcc33",
		width: int = 6,
	) -> ArrowGeometry:
		"""Draw an arrow using coordinates local to a board-sized Tk canvas."""
		geometry = self.geometry(board, uci_move)
		start_x = geometry.start[0] - board.x
		start_y = geometry.start[1] - board.y
		end_x = geometry.end[0] - board.x
		end_y = geometry.end[1] - board.y
		canvas.create_line(
			start_x,
			start_y,
			end_x,
			end_y,
			fill=color,
			width=width,
			arrow="last",
			arrowshape=(18, 22, 8),
			tags="move-arrow",
		)
		return geometry
