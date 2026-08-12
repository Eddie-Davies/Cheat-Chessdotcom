"""Evidence-based side-to-move detection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


WHITE = "white"
BLACK = "black"
UNKNOWN = "unknown"


@dataclass(frozen=True)
class SideToMoveDetection:
	"""Side-to-move result with confidence and contributing signals."""

	side_to_move: str
	confidence: float
	signals: tuple[str, ...] = ()

	@property
	def analysis_ready(self) -> bool:
		"""Whether the result is confident enough for position reconstruction."""
		return self.side_to_move in {WHITE, BLACK} and self.confidence >= 0.65


class SideToMoveDetector:
	"""Combine visible UI and confirmed-history evidence without guessing."""

	def detect(
		self,
		*,
		active_player: str | None = None,
		board_highlight: str | None = None,
		active_clock: str | None = None,
		ui_indicator: str | None = None,
		confirmed_history: Sequence[str] | None = None,
	) -> SideToMoveDetection:
		"""Return white, black, or unknown from available structured evidence."""
		votes = {WHITE: 0.0, BLACK: 0.0}
		signals: list[str] = []
		self._vote(votes, signals, "active_player", active_player, 4.0)
		self._vote(votes, signals, "board_highlight", board_highlight, 3.0)
		self._vote(votes, signals, "active_clock", active_clock, 2.0)
		self._vote(votes, signals, "ui_indicator", ui_indicator, 3.0)
		latest = self._latest_confirmed(confirmed_history)
		self._vote(votes, signals, "history", latest, 1.5)

		total = votes[WHITE] + votes[BLACK]
		if total == 0:
			return SideToMoveDetection(UNKNOWN, 0.0, ())
		margin = abs(votes[WHITE] - votes[BLACK]) / total
		if margin < 0.25:
			return SideToMoveDetection(UNKNOWN, 0.5, tuple(signals))
		winner = WHITE if votes[WHITE] > votes[BLACK] else BLACK
		confidence = min(1.0, 0.5 + margin / 2)
		return SideToMoveDetection(winner, confidence, tuple(signals))

	@staticmethod
	def _vote(
		votes: dict[str, float],
		signals: list[str],
		name: str,
		value: str | None,
		weight: float,
	) -> None:
		if value in {WHITE, BLACK}:
			votes[value] += weight
			signals.append(f"{name}:{value}")

	@staticmethod
	def _latest_confirmed(history: Sequence[str] | None) -> str | None:
		if not history:
			return None
		for value in reversed(history):
			if value in {WHITE, BLACK}:
				return value
		return None