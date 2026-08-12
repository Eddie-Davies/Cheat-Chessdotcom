"""Cross-platform Stockfish integration built on :mod:`python-chess`."""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import chess
import chess.engine


class EngineError(RuntimeError):
	"""Base exception for engine startup and analysis failures."""


class StockfishUnavailableError(EngineError):
	"""Raised when Stockfish cannot be located or started."""


class InvalidFENError(ValueError):
	"""Raised when analysis is requested for an invalid FEN."""


@dataclass(frozen=True)
class EngineLine:
	"""One principal variation returned by the engine."""

	move: str
	san: str
	score: float | None
	mate: int | None
	depth: int
	principal_variation: list[str]


@dataclass(frozen=True)
class EngineAnalysis:
	"""The requested engine analysis, including all MultiPV lines."""

	best_move: str
	best_move_san: str
	score: float | None
	mate: int | None
	depth: int
	lines: list[EngineLine]


def _default_engine_candidates() -> list[str]:
	"""Return platform-neutral Stockfish locations, followed by PATH lookup."""
	project_root = Path(__file__).resolve().parents[3]
	system = platform.system().lower()
	platform_name = {"windows": "windows", "darwin": "macos", "linux": "linux"}.get(
		system, system
	)
	executable_name = "stockfish.exe" if system == "windows" else "stockfish"
	candidates = [
		str(project_root / "engine" / "stockfish" / platform_name / executable_name),
		str(project_root / "engine" / "stockfish" / platform_name / "stockfish"),
	]
	path_engine = shutil.which("stockfish")
	if path_engine:
		candidates.append(path_engine)
	return candidates


class StockfishEngine:
	"""Manage a Stockfish process and expose FEN-based analysis.

	``engine_factory`` is intentionally injectable for deterministic tests and
	for future platform-specific process configuration. It must accept an
	executable path and return a ``chess.engine.SimpleEngine``-compatible object.
	"""

	def __init__(
		self,
		engine_path: str | os.PathLike[str] | None = None,
		*,
		engine_factory: Callable[[str], Any] | None = None,
	) -> None:
		self.engine_path = str(engine_path) if engine_path else None
		self._engine_factory = engine_factory or chess.engine.SimpleEngine.popen_uci
		self._engine: Any | None = None

	@property
	def is_running(self) -> bool:
		"""Whether an engine process is currently managed by this instance."""
		return self._engine is not None

	def start(self) -> None:
		"""Locate and start Stockfish, raising a useful error if unavailable."""
		if self.is_running:
			return

		candidates = [self.engine_path] if self.engine_path else _default_engine_candidates()
		executable = next((candidate for candidate in candidates if candidate and self._is_executable(candidate)), None)
		if executable is None:
			searched = ", ".join(candidate for candidate in candidates if candidate)
			raise StockfishUnavailableError(
				f"Stockfish executable not found. Searched: {searched or 'PATH'}"
			)

		try:
			self._engine = self._engine_factory(executable)
		except (OSError, chess.engine.EngineError) as exc:
			raise StockfishUnavailableError(f"Unable to start Stockfish: {exc}") from exc

	def stop(self) -> None:
		"""Stop Stockfish cleanly; safe to call more than once."""
		if self._engine is None:
			return
		engine, self._engine = self._engine, None
		try:
			engine.quit()
		except (OSError, chess.engine.EngineError):
			pass

	def analyse(
		self,
		fen: str,
		*,
		depth: int | None = None,
		time_ms: int | None = None,
		multipv: int = 1,
	) -> EngineAnalysis:
		"""Analyze ``fen`` using depth, time, or the configured default limit."""
		board = self._parse_fen(fen)
		if depth is not None and depth < 1:
			raise ValueError("depth must be at least 1")
		if time_ms is not None and time_ms <= 0:
			raise ValueError("time_ms must be greater than 0")
		if multipv < 1:
			raise ValueError("multipv must be at least 1")
		if depth is None and time_ms is None:
			depth = 20

		self.start()
		limit = chess.engine.Limit(depth=depth, time=time_ms / 1000 if time_ms else None)
		try:
			raw_infos = self._engine.analyse(board, limit, multipv=multipv)
		except chess.engine.EngineError as exc:
			raise EngineError(f"Stockfish analysis failed: {exc}") from exc

		infos = raw_infos if isinstance(raw_infos, list) else [raw_infos]
		lines = [self._to_line(board, info) for info in infos]
		if not lines:
			raise EngineError("Stockfish returned no analysis lines")
		best_line = lines[0]
		return EngineAnalysis(
			best_move=best_line.move,
			best_move_san=best_line.san,
			score=best_line.score,
			mate=best_line.mate,
			depth=best_line.depth,
			lines=lines,
		)

	@staticmethod
	def _is_executable(candidate: str) -> bool:
		return bool(shutil.which(candidate) or Path(candidate).is_file())

	@staticmethod
	def _parse_fen(fen: str) -> chess.Board:
		try:
			return chess.Board(fen)
		except ValueError as exc:
			raise InvalidFENError(f"Invalid FEN: {exc}") from exc

	@staticmethod
	def _to_line(board: chess.Board, info: dict[str, Any]) -> EngineLine:
		variation: Sequence[chess.Move] = info.get("pv") or []
		if not variation:
			raise EngineError("Stockfish returned an analysis line without a move")
		move = variation[0]
		score = info.get("score")
		pov_score = score.pov(chess.WHITE) if score is not None else None
		mate = pov_score.mate() if pov_score is not None else None
		centipawns = pov_score.score(mate_score=100000) if pov_score is not None else None
		return EngineLine(
			move=move.uci(),
			san=board.san(move),
			score=centipawns / 100 if centipawns is not None and mate is None else None,
			mate=mate,
			depth=int(info.get("depth") or 0),
			principal_variation=[variation_move.uci() for variation_move in variation],
		)

	def __enter__(self) -> "StockfishEngine":
		self.start()
		return self

	def __exit__(self, _exc_type: Any, _exc_value: Any, _traceback: Any) -> None:
		self.stop()
