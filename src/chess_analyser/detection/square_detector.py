"""Map detected board geometry to the 64 screen-space chess squares."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .board_detector import BoardDetection


FILES = "abcdefgh"
ORIENTATIONS = {"white_bottom", "black_bottom", "unknown"}


@dataclass(frozen=True)
class SquareDetection:
	"""Floating-point screen geometry for one algebraic chess square."""

	square: str
	x: float
	y: float
	width: float
	height: float

	@property
	def center(self) -> tuple[float, float]:
		"""Return the square center in screen coordinates."""
		return (self.x + self.width / 2, self.y + self.height / 2)

	@property
	def pixel_bounds(self) -> tuple[int, int, int, int]:
		"""Return rounded half-open pixel bounds ``left, top, right, bottom``."""
		return (
			round(self.x),
			round(self.y),
			round(self.x + self.width),
			round(self.y + self.height),
		)


class SquareDetector:
	"""Create square mappings from a ``BoardDetection`` result."""

	def map_squares(self, board: BoardDetection) -> dict[str, SquareDetection]:
		"""Return all 64 squares keyed by algebraic coordinate.

		``white_bottom`` maps screen top-left to ``a8``. ``black_bottom`` maps
		screen top-left to ``h1``. ``unknown`` uses the normal mapping while
		preserving the unknown orientation in the board result for later phases.
		"""
		orientation = board.orientation if board.orientation in ORIENTATIONS else "unknown"
		column_width = board.width / 8
		row_height = board.height / 8
		squares: dict[str, SquareDetection] = {}
		for screen_row in range(8):
			for screen_column in range(8):
				if orientation == "black_bottom":
					file_index = 7 - screen_column
					rank = screen_row + 1
				else:
					file_index = screen_column
					rank = 8 - screen_row
				name = f"{FILES[file_index]}{rank}"
				squares[name] = SquareDetection(
					square=name,
					x=board.x + screen_column * column_width,
					y=board.y + screen_row * row_height,
					width=column_width,
					height=row_height,
				)
		return squares

	def render_labels(
		self,
		image: np.ndarray,
		board: BoardDetection,
		output_path: str | Path,
		*,
		color: tuple[int, int, int] = (0, 0, 255),
	) -> Path:
		"""Draw square boundaries and algebraic labels onto a screenshot."""
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		result = image[:, :, :3].copy()
		for square in self.map_squares(board).values():
			left, top, right, bottom = square.pixel_bounds
			cv2.rectangle(result, (left, top), (right, bottom), color, 1)
			center_x, center_y = square.center
			cv2.putText(
				result,
				square.square,
				(round(center_x - 10), round(center_y + 5)),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.45,
				color,
				1,
				cv2.LINE_AA,
			)
		path = Path(output_path).expanduser()
		path.parent.mkdir(parents=True, exist_ok=True)
		if not cv2.imwrite(str(path), result):
			raise OSError(f"Unable to save square diagnostic image: {path}")
		return path.resolve()


def main() -> None:
	"""Label all mapped squares in a detected-board diagnostic image."""
	parser = argparse.ArgumentParser(description="Label chess squares in a detected board")
	parser.add_argument("input", type=Path, help="Input screenshot")
	parser.add_argument("output", type=Path, help="Output labelled screenshot")
	parser.add_argument("--x", type=float, required=True, help="Detected board left coordinate")
	parser.add_argument("--y", type=float, required=True, help="Detected board top coordinate")
	parser.add_argument("--width", type=float, required=True, help="Detected board width")
	parser.add_argument("--height", type=float, required=True, help="Detected board height")
	parser.add_argument("--orientation", choices=sorted(ORIENTATIONS), default="white_bottom")
	args = parser.parse_args()
	image = cv2.imread(str(args.input))
	if image is None:
		raise SystemExit(f"Unable to read screenshot: {args.input}")
	board = BoardDetection(args.x, args.y, args.width, args.height, args.width / 8, 1.0, args.orientation)
	output = SquareDetector().render_labels(image, board, args.output)
	print(f"Saved square diagnostic image to {output}")


if __name__ == "__main__":
	main()
