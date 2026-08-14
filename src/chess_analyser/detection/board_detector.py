"""Deterministic chessboard detection using OpenCV and NumPy."""

from __future__ import annotations

import logging
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class BoardDetection:
	"""Detected screen-space chessboard geometry and confidence."""

	x: int
	y: int
	width: int
	height: int
	square_size: float
	confidence: float
	orientation: str = "unknown"


@dataclass(frozen=True)
class _Candidate:
	x: int
	y: int
	width: int
	height: int
	confidence: float


class BoardDetector:
	"""Find an eight-by-eight alternating-square pattern in a screen image."""

	def __init__(
		self,
		*,
		min_board_size: int = 80,
		min_confidence: float = 0.58,
		max_search_dimension: int = 1400,
		logger: logging.Logger | None = None,
	) -> None:
		if min_board_size < 8:
			raise ValueError("min_board_size must be at least 8")
		if not 0 <= min_confidence <= 1:
			raise ValueError("min_confidence must be between 0 and 1")
		self.min_board_size = min_board_size
		self.min_confidence = min_confidence
		self.max_search_dimension = max_search_dimension
		self.logger = logger or logging.getLogger(__name__)

	def detect(self, screen_image: np.ndarray) -> BoardDetection | None:
		"""Return the highest-scoring board candidate, or ``None`` if uncertain."""
		image = self._validate_image(screen_image)
		working, scale = self._resize_for_search(image)
		gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
		integral = cv2.integral(gray, sdepth=cv2.CV_64F)
		gradient_x = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
		gradient_y = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
		candidates = self._find_candidates(working)
		candidates.extend(self._grid_candidates(working))
		scored = [
			self._score_candidate(
				working, candidate, gray=gray, gradient_x=gradient_x, gradient_y=gradient_y, integral=integral
			)
			for candidate in candidates
		]
		scored = [candidate for candidate in scored if candidate is not None]
		if not scored:
			return None
		best = max(
			scored,
			key=lambda candidate: (round(candidate.confidence, 6), candidate.width * candidate.height),
		)
		best = self._snap_candidate_edges(working, best)
		if best.confidence < self.min_confidence:
			self.logger.debug("Rejected board candidate with confidence %.3f", best.confidence)
			return None
		detection = BoardDetection(
			x=round(best.x / scale),
			y=round(best.y / scale),
			width=round(best.width / scale),
			height=round(best.height / scale),
			square_size=best.width / 8 / scale,
			confidence=best.confidence,
		)
		self.logger.info(
			"Board detected at (%d, %d) size %dx%d confidence %.3f",
			detection.x,
			detection.y,
			detection.width,
			detection.height,
			detection.confidence,
		)
		return detection

	def _snap_candidate_edges(self, image: np.ndarray, candidate: _Candidate) -> _Candidate:
		"""Align nearby candidate edges to strong image transitions."""
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		integral = cv2.integral(gray, sdepth=cv2.CV_64F)
		gradient_x = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
		gradient_y = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
		cell_size = max(8, round(candidate.width / 8))
		left = self._strongest_edge(
			gradient_x,
			candidate.x,
			max(0, candidate.y + round(candidate.height * 0.08)),
			min(gray.shape[0], candidate.y + round(candidate.height * 0.92)),
			cell_size,
			vertical=True,
		)
		right = self._strongest_edge(
			gradient_x,
			candidate.x + candidate.width,
			max(0, candidate.y + round(candidate.height * 0.08)),
			min(gray.shape[0], candidate.y + round(candidate.height * 0.92)),
			cell_size,
			vertical=True,
		)
		top = self._strongest_edge(
			gradient_y,
			candidate.y,
			max(0, candidate.x + round(candidate.width * 0.08)),
			min(gray.shape[1], candidate.x + round(candidate.width * 0.92)),
			cell_size,
			vertical=False,
		)
		bottom = self._strongest_edge(
			gradient_y,
			candidate.y + candidate.height,
			max(0, candidate.x + round(candidate.width * 0.08)),
			min(gray.shape[1], candidate.x + round(candidate.width * 0.92)),
			cell_size,
			vertical=False,
		)
		if right <= left or bottom <= top:
			return candidate
		options: list[_Candidate] = []
		for candidate_x in (left, right - candidate.width):
			for candidate_y in (top, bottom - candidate.height):
				if candidate_x < 0 or candidate_y < 0:
					continue
				if candidate_x + candidate.width > image.shape[1] or candidate_y + candidate.height > image.shape[0]:
					continue
				refined = self._score_candidate(
					image,
					(candidate_x, candidate_y, candidate.width, candidate.height),
					gray=gray,
					gradient_x=gradient_x,
					gradient_y=gradient_y,
					integral=integral,
				)
				if refined:
					options.append(refined)
		return max(options, key=lambda item: (round(item.confidence, 6), item.width * item.height)) if options else candidate

	@staticmethod
	def _strongest_edge(
		gradient: np.ndarray,
		center: int,
		band_start: int,
		band_end: int,
		search_radius: int,
		*,
		vertical: bool,
	) -> int:
		start = max(1, center - search_radius // 2)
		axis_length = gradient.shape[1] if vertical else gradient.shape[0]
		end = min(axis_length - 2, center + search_radius // 2)
		if vertical:
			scores = [float(np.median(gradient[band_start:band_end, position - 1 : position + 2])) for position in range(start, end + 1)]
		else:
			scores = [float(np.median(gradient[position - 1 : position + 2, band_start:band_end])) for position in range(start, end + 1)]
		return start + int(np.argmax(scores))

	def draw_diagnostic(
		self,
		screen_image: np.ndarray,
		detection: BoardDetection,
		output_path: str | Path,
	) -> Path:
		"""Draw a detected bounding box and grid, then save a diagnostic image."""
		image = self._validate_image(screen_image).copy()
		x, y, width, height = detection.x, detection.y, detection.width, detection.height
		cv2.rectangle(image, (x, y), (x + width, y + height), (0, 0, 255), 3)
		square_width = width / 8
		square_height = height / 8
		for index in range(1, 8):
			cv2.line(image, (round(x + index * square_width), y), (round(x + index * square_width), y + height), (0, 255, 255), 1)
			cv2.line(image, (x, round(y + index * square_height)), (x + width, round(y + index * square_height)), (0, 255, 255), 1)
		label = f"board confidence={detection.confidence:.2f}"
		cv2.putText(image, label, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
		path = Path(output_path).expanduser()
		path.parent.mkdir(parents=True, exist_ok=True)
		if not cv2.imwrite(str(path), image):
			raise OSError(f"Unable to save diagnostic board image: {path}")
		return path.resolve()

	def _find_candidates(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		edges = cv2.Canny(gray, 40, 140)
		kernel = np.ones((5, 5), dtype=np.uint8)
		edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
		contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		candidates: set[tuple[int, int, int, int]] = set()
		cell_boxes: list[tuple[int, int, int, int]] = []
		height, width = gray.shape
		for contour in contours:
			x, y, candidate_width, candidate_height = cv2.boundingRect(contour)
			if candidate_width < self.min_board_size or candidate_height < self.min_board_size:
				continue
			if candidate_width > width or candidate_height > height:
				continue
			ratio = candidate_width / candidate_height
			if (
				20 <= min(candidate_width, candidate_height) <= min(width, height) / 8
				and 0.82 <= ratio <= 1.22
			):
				cell_boxes.append((x, y, candidate_width, candidate_height))
			if 0.82 <= ratio <= 1.22:
				candidates.add((x, y, candidate_width, candidate_height))
				if min(candidate_width, candidate_height) >= self.min_board_size * 4:
					candidates.update(
						self._square_refinements(
							x,
							y,
							candidate_width,
							candidate_height,
							width,
							height,
						)
					)
		for x, y, cell_width, cell_height in cell_boxes:
			side = round(((cell_width + cell_height) / 2) * 8)
			if side >= self.min_board_size and x + side <= width and y + side <= height:
				candidates.add((x, y, side, side))
		return list(candidates)

	def _grid_candidates(self, image: np.ndarray) -> list[tuple[int, int, int, int]]:
		"""Search square windows when board edges are weak or textured."""
		height, width = image.shape[:2]
		minimum_side = max(self.min_board_size * 2, min(height, width) // 5)
		maximum_side = min(height, width)
		if minimum_side > maximum_side:
			return []
		sides = np.unique(np.linspace(minimum_side, maximum_side, 16, dtype=int))
		candidates: list[tuple[int, int, int, int]] = []
		for side in sides:
			step = max(12, side // 10)
			for y in range(0, height - side + 1, step):
				for x in range(0, width - side + 1, step):
					candidates.append((x, y, int(side), int(side)))
		return candidates

	@staticmethod
	def _square_refinements(
		x: int,
		y: int,
		width: int,
		height: int,
		image_width: int,
		image_height: int,
	) -> Iterable[tuple[int, int, int, int]]:
		"""Search a bounded neighborhood for a square subregion of a broad contour."""
		minimum_side = min(width, height)
		for fraction in np.linspace(0.76, 0.99, 8):
			side = round(minimum_side * float(fraction))
			if side < 80:
				continue
			horizontal_start = x - round(minimum_side * 0.12)
			horizontal_end = x + width - side + round(minimum_side * 0.12)
			vertical_start = y - round(minimum_side * 0.12)
			vertical_end = y + height - side + round(minimum_side * 0.12)
			for candidate_x in np.linspace(horizontal_start, horizontal_end, 7, dtype=int):
				for candidate_y in np.linspace(vertical_start, vertical_end, 7, dtype=int):
					if (
						candidate_x >= 0
						and candidate_y >= 0
						and candidate_x + side <= image_width
						and candidate_y + side <= image_height
					):
						yield (int(candidate_x), int(candidate_y), side, side)

	def _score_candidate(
		self,
		image: np.ndarray,
		candidate: tuple[int, int, int, int],
		*,
		gray: np.ndarray | None = None,
		gradient_x: np.ndarray | None = None,
		gradient_y: np.ndarray | None = None,
		integral: np.ndarray | None = None,
	) -> _Candidate | None:
		x, y, width, height = candidate
		cell_width = width / 8
		cell_height = height / 8
		if min(cell_width, cell_height) < 8:
			return None
		if gray is None:
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		if integral is None:
			integral = cv2.integral(gray, sdepth=cv2.CV_64F)
		index = np.arange(8)
		lefts = np.round(x + (index + 0.25) * cell_width).astype(np.int64)
		rights = np.round(x + (index + 0.75) * cell_width).astype(np.int64)
		tops = np.round(y + (index + 0.25) * cell_height).astype(np.int64)
		bottoms = np.round(y + (index + 0.75) * cell_height).astype(np.int64)
		if rights.max() > gray.shape[1] or bottoms.max() > gray.shape[0] or lefts.min() < 0 or tops.min() < 0:
			return None
		# Summed-area-table lookup avoids 64 separate np.mean calls per candidate.
		sums = (
			integral[bottoms[:, None], rights[None, :]]
			- integral[tops[:, None], rights[None, :]]
			- integral[bottoms[:, None], lefts[None, :]]
			+ integral[tops[:, None], lefts[None, :]]
		)
		areas = np.maximum((bottoms[:, None] - tops[:, None]) * (rights[None, :] - lefts[None, :]), 1)
		cells = (sums / areas).astype(np.float32)
		cell_std = float(np.std(cells))
		if cell_std < 4:
			return None
		checker = np.fromfunction(lambda row, column: (-1.0) ** (row + column), (8, 8))
		checker_score = float(abs(np.mean((cells - np.mean(cells)) * checker)) / (cell_std + 1e-6))
		checker_score = float(np.clip(checker_score, 0, 1))
		adjacent_difference = np.concatenate(
			[np.abs(np.diff(cells, axis=0)).ravel(), np.abs(np.diff(cells, axis=1)).ravel()]
		)
		contrast_score = float(np.clip(np.mean(adjacent_difference) / (cell_std + 1e-6), 0, 1))
		boundary_values: list[float] = []
		for index in range(1, 8):
			vertical_boundary = round(x + index * cell_width)
			horizontal_boundary = round(y + index * cell_height)
			vertical_left = gray[round(y + 0.1 * height) : round(y + 0.9 * height), vertical_boundary - 2 : vertical_boundary]
			vertical_right = gray[round(y + 0.1 * height) : round(y + 0.9 * height), vertical_boundary : vertical_boundary + 2]
			horizontal_top = gray[horizontal_boundary - 2 : horizontal_boundary, round(x + 0.1 * width) : round(x + 0.9 * width)]
			horizontal_bottom = gray[horizontal_boundary : horizontal_boundary + 2, round(x + 0.1 * width) : round(x + 0.9 * width)]
			boundary_values.extend(
				[
					float(np.mean(np.abs(vertical_left.astype(np.float32) - vertical_right.astype(np.float32)))),
					float(np.mean(np.abs(horizontal_top.astype(np.float32) - horizontal_bottom.astype(np.float32)))),
				]
			)
		boundary_score = float(np.clip(np.mean(boundary_values) / (cell_std + 1e-6), 0, 1))
		if gradient_x is None:
			gradient_x = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
		if gradient_y is None:
			gradient_y = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
		vertical_band = slice(round(y + 0.08 * height), round(y + 0.92 * height))
		horizontal_band = slice(round(x + 0.08 * width), round(x + 0.92 * width))
		left_edge = float(np.median(gradient_x[vertical_band, max(0, x - 1) : x + 2]))
		right_edge = float(np.median(gradient_x[vertical_band, max(0, x + width - 1) : x + width + 2]))
		top_edge = float(np.median(gradient_y[max(0, y - 1) : y + 2, horizontal_band]))
		bottom_edge = float(
			np.median(gradient_y[max(0, y + height - 1) : y + height + 2, horizontal_band])
		)
		outer_edge_score = float(
			np.sqrt(
				np.clip(left_edge / 80, 0, 1)
				* np.clip(right_edge / 80, 0, 1)
				* np.clip(top_edge / 80, 0, 1)
				* np.clip(bottom_edge / 80, 0, 1)
			)
		)
		geometry_score = float(np.exp(-3.5 * abs(np.log(width / height))))
		confidence = float(
			np.clip(
				0.40 * checker_score
				+ 0.15 * contrast_score
				+ 0.15 * boundary_score
				+ 0.20 * outer_edge_score
				+ 0.10 * geometry_score,
				0,
				1,
			)
		)
		return _Candidate(x, y, width, height, confidence)

	def _resize_for_search(self, image: np.ndarray) -> tuple[np.ndarray, float]:
		height, width = image.shape[:2]
		largest_dimension = max(height, width)
		if largest_dimension <= self.max_search_dimension:
			return image, 1.0
		scale = self.max_search_dimension / largest_dimension
		resized = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
		return resized, scale

	@staticmethod
	def _validate_image(screen_image: np.ndarray) -> np.ndarray:
		if not isinstance(screen_image, np.ndarray):
			raise TypeError("screen_image must be a numpy.ndarray")
		if screen_image.ndim != 3 or screen_image.shape[2] not in (3, 4):
			raise ValueError("screen_image must be a color image with 3 or 4 channels")
		if screen_image.shape[0] < 8 or screen_image.shape[1] < 8:
			raise ValueError("screen_image is too small")
		return screen_image[:, :, :3]


def main() -> None:
	"""Detect and annotate a screenshot from the command line."""
	parser = argparse.ArgumentParser(description="Detect a chessboard in a screenshot")
	parser.add_argument("input", type=Path, help="Input screenshot path")
	parser.add_argument("output", type=Path, help="Output path for the annotated screenshot")
	args = parser.parse_args()
	image = cv2.imread(str(args.input))
	if image is None:
		raise SystemExit(f"Unable to read screenshot: {args.input}")
	detector = BoardDetector()
	detection = detector.detect(image)
	if detection is None:
		raise SystemExit("No chessboard detected")
	output = detector.draw_diagnostic(image, detection, args.output)
	print(f"Detected board: {detection}")
	print(f"Saved diagnostic image to {output}")


if __name__ == "__main__":
	main()
