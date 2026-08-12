"""Temporal position confirmation and duplicate-analysis suppression."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from chess_analyser.chess.position import ChessPosition


@dataclass(frozen=True)
class StabilityUpdate:
	"""Result of submitting one detected position frame."""

	position_hash: str
	frame_count: int
	stable: bool
	transition: bool
	should_analyse: bool
	position: ChessPosition


class PositionTracker:
	"""Confirm positions across frames and suppress duplicate analyses."""

	def __init__(
		self,
		*,
		stability_frames: int = 3,
		debounce_ms: int = 0,
		clock: Any = time.monotonic,
	) -> None:
		if stability_frames < 1:
			raise ValueError("stability_frames must be at least 1")
		if debounce_ms < 0:
			raise ValueError("debounce_ms must not be negative")
		self.stability_frames = stability_frames
		self.debounce_ms = debounce_ms
		self._clock = clock
		self._candidate_hash: str | None = None
		self._candidate_position: ChessPosition | None = None
		self._candidate_frames = 0
		self._candidate_started_at: float | None = None
		self._stable_hash: str | None = None
		self._analysed_hashes: set[str] = set()

	@property
	def stable_hash(self) -> str | None:
		"""Return the last temporally confirmed position hash."""
		return self._stable_hash

	@property
	def candidate_frames(self) -> int:
		"""Return the number of consecutive frames in the current candidate."""
		return self._candidate_frames

	def update(
		self,
		position: ChessPosition | Any,
		*,
		timestamp: float | None = None,
	) -> StabilityUpdate:
		"""Submit one position frame and return its temporal status.

		A changed hash immediately enters transition state. It can only become
		stable after the configured frame count and debounce interval are met.
		"""
		board = self._extract_position(position)
		current_time = self._clock() if timestamp is None else timestamp
		position_hash = board.position_hash()
		transition = self._stable_hash is not None and position_hash != self._stable_hash
		if position_hash != self._candidate_hash:
			self._candidate_hash = position_hash
			self._candidate_position = board
			self._candidate_frames = 1
			self._candidate_started_at = current_time
		else:
			self._candidate_frames += 1

		elapsed_ms = 0.0
		if self._candidate_started_at is not None:
			elapsed_ms = max(0.0, (current_time - self._candidate_started_at) * 1000)
		stable = (
			self._candidate_frames >= self.stability_frames
			and elapsed_ms >= self.debounce_ms
		)
		should_analyse = False
		if stable and self._stable_hash != position_hash:
			self._stable_hash = position_hash
			if position_hash not in self._analysed_hashes:
				self._analysed_hashes.add(position_hash)
				should_analyse = True

		return StabilityUpdate(
			position_hash=position_hash,
			frame_count=self._candidate_frames,
			stable=stable,
			transition=transition,
			should_analyse=should_analyse,
			position=board,
		)

	def reset(self) -> None:
		"""Forget the current candidate and stable position, including cache."""
		self._candidate_hash = None
		self._candidate_position = None
		self._candidate_frames = 0
		self._candidate_started_at = None
		self._stable_hash = None
		self._analysed_hashes.clear()

	@staticmethod
	def _extract_position(value: ChessPosition | Any) -> ChessPosition:
		if isinstance(value, ChessPosition):
			return value
		position = getattr(value, "position", None)
		if isinstance(position, ChessPosition):
			return position
		raise TypeError("position must be ChessPosition or contain a ChessPosition in .position")
