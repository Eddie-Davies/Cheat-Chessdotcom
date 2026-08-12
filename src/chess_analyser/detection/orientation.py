"""Evidence-based chessboard orientation detection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


WHITE_BOTTOM = "white_bottom"
BLACK_BOTTOM = "black_bottom"
UNKNOWN = "unknown"
ORIENTATIONS = {WHITE_BOTTOM, BLACK_BOTTOM, UNKNOWN}


@dataclass(frozen=True)
class OrientationDetection:
	"""Orientation result, confidence, and the signals that produced it."""

	orientation: str
	confidence: float
	signals: tuple[str, ...] = ()


class OrientationDetector:
	"""Combine independent orientation hints without assuming a default."""

	def detect(
		self,
		*,
		labels: Mapping[str, str] | None = None,
		corner_pieces: Mapping[str, str] | None = None,
		orientation_history: Sequence[str] | None = None,
		previous_orientation: str | None = None,
	) -> OrientationDetection:
		"""Determine orientation from labels, optional pieces, and history.

		``labels`` may contain ``top``, ``bottom``, ``left``, and ``right``
		observations. ``corner_pieces`` may contain screen positions such as
		``top_left`` and ``bottom_left`` with values like ``white_rook``.
		These are evidence interfaces for later CV/piece-recognition phases;
		missing or conflicting evidence returns ``unknown``.
		"""
		votes = {WHITE_BOTTOM: 0.0, BLACK_BOTTOM: 0.0}
		signals: list[str] = []
		self._add_label_votes(votes, signals, labels)
		self._add_piece_votes(votes, signals, corner_pieces)
		history_value = previous_orientation or self._latest_history(orientation_history)
		if history_value in (WHITE_BOTTOM, BLACK_BOTTOM):
			votes[history_value] += 1.0
			signals.append(f"history:{history_value}")

		total = votes[WHITE_BOTTOM] + votes[BLACK_BOTTOM]
		if total == 0 or abs(votes[WHITE_BOTTOM] - votes[BLACK_BOTTOM]) < total * 0.25:
			return OrientationDetection(UNKNOWN, 0.0 if total == 0 else 0.5, tuple(signals))
		orientation = max(votes, key=votes.get)
		confidence = min(1.0, 0.5 + abs(votes[WHITE_BOTTOM] - votes[BLACK_BOTTOM]) / (2 * total))
		return OrientationDetection(orientation, confidence, tuple(signals))

	@staticmethod
	def _add_label_votes(
		votes: dict[str, float],
		signals: list[str],
		labels: Mapping[str, str] | None,
	) -> None:
		if not labels:
			return
		for side, value in labels.items():
			text = str(value).lower()
			if side in {"left", "right"}:
				if "a" in text or "1" in text:
					votes[WHITE_BOTTOM] += 3.0
					signals.append(f"label:{side}=white_bottom")
				elif "h" in text or "8" in text:
					votes[BLACK_BOTTOM] += 3.0
					signals.append(f"label:{side}=black_bottom")
			elif side == "bottom":
				if "1" in text:
					votes[WHITE_BOTTOM] += 3.0
					signals.append("label:bottom=white_bottom")
				elif "8" in text:
					votes[BLACK_BOTTOM] += 3.0
					signals.append("label:bottom=black_bottom")

	@staticmethod
	def _add_piece_votes(
		votes: dict[str, float],
		signals: list[str],
		corner_pieces: Mapping[str, str] | None,
	) -> None:
		if not corner_pieces:
			return
		for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
			piece = str(corner_pieces.get(corner, "")).lower()
			if not piece:
				continue
			if corner.startswith("bottom") and piece.startswith("white_"):
				votes[WHITE_BOTTOM] += 2.0
				signals.append(f"piece:{corner}=white_bottom")
			elif corner.startswith("bottom") and piece.startswith("black_"):
				votes[BLACK_BOTTOM] += 2.0
				signals.append(f"piece:{corner}=black_bottom")
			elif corner.startswith("top") and piece.startswith("black_"):
				votes[WHITE_BOTTOM] += 1.0
				signals.append(f"piece:{corner}=white_bottom")
			elif corner.startswith("top") and piece.startswith("white_"):
				votes[BLACK_BOTTOM] += 1.0
				signals.append(f"piece:{corner}=black_bottom")

	@staticmethod
	def _latest_history(history: Sequence[str] | None) -> str | None:
		if not history:
			return None
		for value in reversed(history):
			if value in (WHITE_BOTTOM, BLACK_BOTTOM):
				return value
		return None
