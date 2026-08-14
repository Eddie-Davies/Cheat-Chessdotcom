"""Deterministic visual signals from the Chess.com game layout."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .board_detector import BoardDetection


TOP = "top"
BOTTOM = "bottom"
UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClockSignal:
	"""Which board-side clock appears to be active."""

	side: str
	confidence: float
	active_score: float
	signals: tuple[str, ...] = ()


class ChessComClockDetector:
	"""Read active/inactive clock styling relative to detected board geometry."""

	def detect(self, image: np.ndarray, board: BoardDetection) -> ClockSignal:
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		top_score = self._active_score(image, board, TOP)
		bottom_score = self._active_score(image, board, BOTTOM)
		margin = abs(top_score - bottom_score)
		if margin < 0.02:
			return ClockSignal(UNKNOWN, 0.5 if top_score or bottom_score else 0.0, max(top_score, bottom_score))
		active_side = TOP if top_score > bottom_score else BOTTOM
		confidence = min(1.0, 0.5 + margin)
		return ClockSignal(
			active_side,
			confidence,
			max(top_score, bottom_score),
			(
				f"clock:{TOP}={top_score:.3f}",
				f"clock:{BOTTOM}={bottom_score:.3f}",
			),
		)

	@staticmethod
	def _active_score(image: np.ndarray, board: BoardDetection, side: str) -> float:
		width = max(1, round(board.width * 0.18))
		left = round(board.x + board.width - width)
		if side == TOP:
			top = round(board.y - board.height * 0.065)
		else:
			top = round(board.y + board.height + board.height * 0.01)
		bottom = top + max(8, round(board.height * 0.055))
		left = max(0, left)
		top = max(0, top)
		bottom = min(image.shape[0], bottom)
		right = min(image.shape[1], left + width)
		if bottom <= top or right <= left:
			return 0.0
		gray = cv2.cvtColor(image[top:bottom, left:right, :3], cv2.COLOR_BGR2GRAY)
		bright_ratio = float(np.mean(gray >= 200))
		dark_ratio = float(np.mean(gray <= 80))
		if bright_ratio >= 0.25:
			return 1.0
		if dark_ratio >= 0.75:
			return min(1.0, bright_ratio * 8.0)
		return bright_ratio * 0.5