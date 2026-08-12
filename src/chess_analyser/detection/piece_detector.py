"""Phase 8 occupancy detection without exact piece classification."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .square_detector import SquareDetection


EMPTY = "empty"
OCCUPIED = "occupied"
UNCERTAIN = "uncertain"
STATUSES = {EMPTY, OCCUPIED, UNCERTAIN}


@dataclass(frozen=True)
class OccupancyDetection:
	"""Occupancy result for one square, including evidence measurements."""

	square: str
	status: str
	confidence: float
	foreground_ratio: float
	edge_ratio: float


class OccupancyDetector:
	"""Determine whether mapped square regions contain foreground content."""

	def __init__(
		self,
		*,
		inset_ratio: float = 0.08,
		occupied_threshold: float = 0.58,
		empty_threshold: float = 0.30,
	) -> None:
		if not 0 <= inset_ratio < 0.5:
			raise ValueError("inset_ratio must be between 0 and 0.5")
		if not 0 <= empty_threshold < occupied_threshold <= 1:
			raise ValueError("thresholds must satisfy 0 <= empty < occupied <= 1")
		self.inset_ratio = inset_ratio
		self.occupied_threshold = occupied_threshold
		self.empty_threshold = empty_threshold

	def detect(
		self,
		image: np.ndarray,
		squares: Mapping[str, SquareDetection],
	) -> dict[str, OccupancyDetection]:
		"""Return occupancy results for every supplied square region."""
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		if not squares:
			return {}
		return {name: self._detect_square(image, square) for name, square in squares.items()}

	def render_diagnostic(
		self,
		image: np.ndarray,
		squares: Mapping[str, SquareDetection],
		results: Mapping[str, OccupancyDetection],
		output_path: str | Path,
	) -> Path:
		"""Draw green occupied, gray empty, and yellow uncertain square regions."""
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		output = image[:, :, :3].copy()
		colors = {OCCUPIED: (0, 210, 0), EMPTY: (150, 150, 150), UNCERTAIN: (0, 215, 255)}
		for name, square in squares.items():
			result = results[name]
			left, top, right, bottom = square.pixel_bounds
			color = colors[result.status]
			cv2.rectangle(output, (left, top), (right, bottom), color, 2)
			cv2.putText(
				output,
				f"{name}:{result.status[0].upper()}",
				(round(square.center[0] - 12), round(square.center[1])),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.38,
				color,
				1,
				cv2.LINE_AA,
			)
		path = Path(output_path).expanduser()
		path.parent.mkdir(parents=True, exist_ok=True)
		if not cv2.imwrite(str(path), output):
			raise OSError(f"Unable to save occupancy diagnostic image: {path}")
		return path.resolve()

	def _detect_square(self, image: np.ndarray, square: SquareDetection) -> OccupancyDetection:
		left, top, right, bottom = square.pixel_bounds
		left = max(0, left)
		top = max(0, top)
		right = min(image.shape[1], right)
		bottom = min(image.shape[0], bottom)
		patch = image[top:bottom, left:right, :3]
		if patch.shape[0] < 8 or patch.shape[1] < 8:
			return OccupancyDetection(square.square, UNCERTAIN, 0.0, 0.0, 0.0)

		height, width = patch.shape[:2]
		inset_y = max(1, round(height * self.inset_ratio))
		inset_x = max(1, round(width * self.inset_ratio))
		inner = patch[inset_y : height - inset_y, inset_x : width - inset_x]
		inner_lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB).astype(np.float32)
		border = np.concatenate(
			[
				inner_lab[: max(1, inner.shape[0] // 8), :, :].reshape(-1, 3),
				inner_lab[-max(1, inner.shape[0] // 8) :, :, :].reshape(-1, 3),
				inner_lab[:, : max(1, inner.shape[1] // 8), :].reshape(-1, 3),
				inner_lab[:, -max(1, inner.shape[1] // 8) :, :].reshape(-1, 3),
			]
		)
		background = np.median(border, axis=0)
		background_spread = float(np.median(np.linalg.norm(border - background, axis=1)))
		distance = np.linalg.norm(inner_lab - background, axis=2)
		threshold = max(10.0, background_spread * 2.5 + 5.0)
		foreground = (distance > threshold).astype(np.uint8) * 255
		foreground = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
		foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
		foreground_ratio = float(np.count_nonzero(foreground) / foreground.size)
		edges = cv2.Canny(cv2.cvtColor(inner, cv2.COLOR_BGR2GRAY), 40, 120)
		edge_ratio = float(np.count_nonzero(edges) / edges.size)
		components, labels, stats, _ = cv2.connectedComponentsWithStats(foreground)
		largest_ratio = 0.0
		if components > 1:
			largest_ratio = float(np.max(stats[1:, cv2.CC_STAT_AREA]) / foreground.size)
		activity = np.clip(foreground_ratio * 2.5 + largest_ratio * 1.5 + edge_ratio * 2.0, 0, 1)
		if activity >= self.occupied_threshold:
			status = OCCUPIED
		elif activity <= self.empty_threshold:
			status = EMPTY
		else:
			status = UNCERTAIN
		confidence = float(np.clip(abs(activity - 0.5) * 2, 0, 1))
		return OccupancyDetection(square.square, status, confidence, foreground_ratio, edge_ratio)


def main() -> None:
	"""Run occupancy detection and render a diagnostic image."""
	parser = argparse.ArgumentParser(description="Detect occupied chess squares")
	parser.add_argument("input", type=Path)
	parser.add_argument("output", type=Path)
	parser.add_argument("--x", type=float, required=True)
	parser.add_argument("--y", type=float, required=True)
	parser.add_argument("--width", type=float, required=True)
	parser.add_argument("--height", type=float, required=True)
	image = cv2.imread(str((args := parser.parse_args()).input))
	if image is None:
		raise SystemExit(f"Unable to read screenshot: {args.input}")
	from .board_detector import BoardDetection
	from .square_detector import SquareDetector
	board = BoardDetection(args.x, args.y, args.width, args.height, args.width / 8, 1.0, "white_bottom")
	squares = SquareDetector().map_squares(board)
	detector = OccupancyDetector()
	results = detector.detect(image, squares)
	output = detector.render_diagnostic(image, squares, results, args.output)
	print(f"Saved occupancy diagnostic image to {output}")


if __name__ == "__main__":
	main()
