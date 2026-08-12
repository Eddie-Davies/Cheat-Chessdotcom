"""Phase 8 occupancy and Phase 9 template-based piece recognition."""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
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


PIECE_NAMES = ("pawn", "knight", "bishop", "rook", "queen", "king")
PIECE_COLORS = ("white", "black")


@dataclass(frozen=True)
class PieceDetection:
	"""Exact piece prediction for one occupied square."""

	square: str
	piece: str
	confidence: float


@dataclass(frozen=True)
class _TemplateFeatures:
	piece: str
	mask: np.ndarray
	contour: np.ndarray | None
	color_polarity: float


class PieceDetector(ABC):
	"""Replaceable interface for exact piece recognition implementations."""

	@abstractmethod
	def detect(
		self,
		image: np.ndarray,
		squares: Mapping[str, SquareDetection],
		occupied_squares: Mapping[str, OccupancyDetection] | set[str] | None = None,
	) -> dict[str, PieceDetection]:
		"""Predict piece type for occupied square regions."""


class TemplatePieceDetector(PieceDetector):
	"""Deterministic piece recognition using normalized silhouette templates."""

	def __init__(self, template_dir: str | Path) -> None:
		self.template_dir = Path(template_dir)
		self.templates = self._load_templates()
		if not self.templates:
			raise ValueError(f"No piece templates found in {self.template_dir}")

	def detect(
		self,
		image: np.ndarray,
		squares: Mapping[str, SquareDetection],
		occupied_squares: Mapping[str, OccupancyDetection] | set[str] | None = None,
	) -> dict[str, PieceDetection]:
		"""Recognize only supplied occupied squares; do not classify empty squares."""
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		occupied_names = self._occupied_names(squares, occupied_squares)
		results: dict[str, PieceDetection] = {}
		for name in occupied_names:
			features = self._extract_features(image, squares[name])
			if features.contour is None:
				results[name] = PieceDetection(name, "unknown", 0.0)
				continue
			scores = sorted(
				((self._score(features, template), template.piece) for template in self.templates),
				reverse=True,
			)
			best_score, best_piece = scores[0]
			second_score = scores[1][0] if len(scores) > 1 else 0.0
			confidence = float(np.clip(0.7 * best_score + 0.3 * max(0.0, best_score - second_score), 0, 1))
			results[name] = PieceDetection(name, best_piece, confidence)
		return results

	def render_diagnostic(
		self,
		image: np.ndarray,
		squares: Mapping[str, SquareDetection],
		results: Mapping[str, PieceDetection],
		output_path: str | Path,
	) -> Path:
		"""Draw piece name and confidence on each recognized square."""
		output = image[:, :, :3].copy()
		for name, result in results.items():
			square = squares[name]
			left, top, right, bottom = square.pixel_bounds
			cv2.rectangle(output, (left, top), (right, bottom), (255, 0, 255), 2)
			cv2.putText(
				output,
				f"{result.piece} {result.confidence:.2f}",
				(left + 3, max(top + 16, round(square.center[1]))),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.42,
				(255, 0, 255),
				1,
				cv2.LINE_AA,
			)
		path = Path(output_path).expanduser()
		path.parent.mkdir(parents=True, exist_ok=True)
		if not cv2.imwrite(str(path), output):
			raise OSError(f"Unable to save piece diagnostic image: {path}")
		return path.resolve()

	def _load_templates(self) -> list[_TemplateFeatures]:
		templates: list[_TemplateFeatures] = []
		for color in PIECE_COLORS:
			for piece in PIECE_NAMES:
				path = self.template_dir / color / f"{piece}.png"
				image = cv2.imread(str(path))
				if image is not None:
					features = self._extract_features_from_image(f"{color}_{piece}", image)
					if features.contour is not None:
						templates.append(features)
		return templates

	@staticmethod
	def _occupied_names(
		squares: Mapping[str, SquareDetection],
		occupied_squares: Mapping[str, OccupancyDetection] | set[str] | None,
	) -> set[str]:
		if occupied_squares is None:
			return set(squares)
		if isinstance(occupied_squares, Mapping):
			return {name for name, result in occupied_squares.items() if result.status == OCCUPIED}
		return set(occupied_squares)

	def _extract_features(self, image: np.ndarray, square: SquareDetection) -> _TemplateFeatures:
		left, top, right, bottom = square.pixel_bounds
		patch = image[max(0, top) : min(image.shape[0], bottom), max(0, left) : min(image.shape[1], right), :3]
		return self._extract_features_from_image(square.square, patch)

	@staticmethod
	def _extract_features_from_image(name: str, patch: np.ndarray) -> _TemplateFeatures:
		if patch.ndim != 3 or min(patch.shape[:2]) < 8:
			return _TemplateFeatures(name, np.zeros((96, 96), np.uint8), None, 0.0)
		height, width = patch.shape[:2]
		inset_y = max(1, round(height * 0.08))
		inset_x = max(1, round(width * 0.08))
		inner = patch[inset_y : height - inset_y, inset_x : width - inset_x]
		lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB).astype(np.float32)
		border = np.concatenate(
			[
				lab[: max(1, lab.shape[0] // 8)].reshape(-1, 3),
				lab[-max(1, lab.shape[0] // 8) :].reshape(-1, 3),
				lab[:, : max(1, lab.shape[1] // 8)].reshape(-1, 3),
				lab[:, -max(1, lab.shape[1] // 8) :].reshape(-1, 3),
			]
		)
		background = np.median(border, axis=0)
		distance = np.linalg.norm(lab - background, axis=2)
		threshold = max(10.0, float(np.median(np.linalg.norm(border - background, axis=1))) * 2.5 + 5.0)
		mask = (distance > threshold).astype(np.uint8) * 255
		mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
		mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		if not contours:
			return _TemplateFeatures(name, cv2.resize(mask, (96, 96)), None, 0.0)
		contour = max(contours, key=cv2.contourArea)
		foreground = lab[:, :, 0][mask > 0]
		polarity = float((np.median(foreground) - background[0]) / 100) if foreground.size else 0.0
		return _TemplateFeatures(name, cv2.resize(mask, (96, 96), interpolation=cv2.INTER_NEAREST), contour, polarity)

	@staticmethod
	def _score(sample: _TemplateFeatures, template: _TemplateFeatures) -> float:
		if sample.contour is None or template.contour is None:
			return 0.0
		shape_distance = cv2.matchShapes(sample.contour, template.contour, cv2.CONTOURS_MATCH_I1, 0.0)
		shape_score = float(np.exp(-4.0 * min(shape_distance, 2.0)))
		mask_score = float(np.mean(sample.mask == template.mask))
		color_score = float(np.clip(1.0 - abs(sample.color_polarity - template.color_polarity) / 1.5, 0, 1))
		return float(np.clip(0.55 * shape_score + 0.25 * mask_score + 0.20 * color_score, 0, 1))


def main() -> None:
	"""Run occupancy and template piece detection, then render diagnostics."""
	parser = argparse.ArgumentParser(description="Recognize chess pieces in a board screenshot")
	parser.add_argument("input", type=Path)
	parser.add_argument("output", type=Path)
	parser.add_argument("--templates", type=Path, default=Path("assets/piece_templates"))
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
	piece_detector = TemplatePieceDetector(args.templates)
	piece_results = piece_detector.detect(image, squares, results)
	output = piece_detector.render_diagnostic(image, squares, piece_results, args.output)
	print(f"Saved piece diagnostic image to {output}")


if __name__ == "__main__":
	main()
