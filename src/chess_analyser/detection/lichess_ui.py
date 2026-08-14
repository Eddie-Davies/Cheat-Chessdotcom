"""Deterministic visual signals from the Lichess game layout.

Calibrated from two real screenshots: one mid-game as Black (black_bottom,
own turn) and one as White (white_bottom, own turn). Both show a thick
green-tinted background behind the currently active player's clock box in
the right-hand sidebar. Only the "own turn" case has been directly verified;
the opposite (opponent's turn, top clock active) is inferred by symmetry of
the same widget and has not yet been confirmed against a real screenshot.
"""

from __future__ import annotations

import cv2
import numpy as np

from .board_detector import BoardDetection
from .chesscom_ui import BOTTOM, TOP, UNKNOWN, ClockSignal


class LichessClockDetector:
	"""Locate the active player's clock by its green-tinted background band."""

	def __init__(self, *, min_band_rows: int = 20, green_threshold: float = 5.0) -> None:
		self.min_band_rows = min_band_rows
		self.green_threshold = green_threshold

	def detect(self, image: np.ndarray, board: BoardDetection) -> ClockSignal:
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise TypeError("image must be a color numpy.ndarray")
		left = round(board.x + board.width * 1.011)
		right = round(board.x + board.width * 1.49)
		top = round(board.y)
		bottom = round(board.y + board.height)
		left = max(0, left)
		top = max(0, top)
		right = min(image.shape[1], right)
		bottom = min(image.shape[0], bottom)
		if right <= left or bottom <= top:
			return ClockSignal(UNKNOWN, 0.0, 0.0)

		strip = image[top:bottom, left:right, :3].astype(np.float32)
		row_bgr = strip.mean(axis=1)
		green_score = row_bgr[:, 1] - (row_bgr[:, 0] + row_bgr[:, 2]) / 2
		band = self._largest_green_band(green_score)
		if band is None:
			return ClockSignal(UNKNOWN, 0.0, 0.0)

		start, end = band
		center_fraction = ((start + end) / 2) / strip.shape[0]
		side = BOTTOM if center_fraction > 0.5 else TOP
		confidence = float(np.clip(0.5 + abs(center_fraction - 0.5), 0.5, 0.95))
		return ClockSignal(
			side,
			confidence,
			float(green_score[start : end + 1].mean()),
			(f"green_band_center_fraction={center_fraction:.2f}",),
		)

	def _largest_green_band(self, green_score: np.ndarray) -> tuple[int, int] | None:
		rows = np.where(green_score > self.green_threshold)[0]
		if rows.size == 0:
			return None
		splits = np.where(np.diff(rows) > 8)[0]
		groups = np.split(rows, splits + 1)
		candidates = [group for group in groups if len(group) >= self.min_band_rows]
		if not candidates:
			return None
		best = max(candidates, key=lambda group: green_score[group].mean())
		return int(best[0]), int(best[-1])
