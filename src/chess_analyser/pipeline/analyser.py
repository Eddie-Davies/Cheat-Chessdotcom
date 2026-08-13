"""Asynchronous automatic screen-to-analysis pipeline."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from chess_analyser.chess import PositionDetection, PositionReconstructor
from chess_analyser.detection import (
	BoardDetector,
	OccupancyDetector,
	OrientationDetector,
	SideToMoveDetector,
	SquareDetector,
	TemplatePieceDetector,
)
from chess_analyser.engine import EngineAnalysis, StockfishEngine

from .position_tracker import PositionTracker, StabilityUpdate


SEARCHING = "SEARCHING"
BOARD_DETECTED = "BOARD_DETECTED"
DETECTING_POSITION = "DETECTING_POSITION"
POSITION_UNCERTAIN = "POSITION_UNCERTAIN"
POSITION_STABLE = "POSITION_STABLE"
ANALYSING = "ANALYSING"
ANALYSIS_READY = "ANALYSIS_READY"
ERROR = "ERROR"


@dataclass(frozen=True)
class PipelineEvent:
	"""Thread-safe event payload emitted by the pipeline."""

	state: str
	message: str = ""
	board: Any | None = None
	position: PositionDetection | None = None
	stability: StabilityUpdate | None = None
	analysis: EngineAnalysis | None = None
	error: Exception | None = None


class AutomaticAnalysisPipeline:
	"""Connect capture, CV, position validation, stability, and engine analysis."""

	def __init__(
		self,
		*,
		capture: Any,
		board_detector: Any | None = None,
		square_detector: Any | None = None,
		orientation_detector: Any | None = None,
		occupancy_detector: Any | None = None,
		piece_detector: Any | None = None,
		position_reconstructor: Any | None = None,
		side_to_move_detector: Any | None = None,
		position_tracker: PositionTracker | None = None,
		engine: Any | None = None,
		capture_interval_ms: int = 100,
		board_confidence_threshold: float = 0.7,
		piece_confidence_threshold: float = 0.55,
		event_callback: Callable[[PipelineEvent], None] | None = None,
		logger: logging.Logger | None = None,
	) -> None:
		if capture_interval_ms < 0:
			raise ValueError("capture_interval_ms must not be negative")
		self.capture = capture
		self.board_detector = board_detector or BoardDetector()
		self.square_detector = square_detector or SquareDetector()
		self.orientation_detector = orientation_detector or OrientationDetector()
		self.occupancy_detector = occupancy_detector or OccupancyDetector()
		self.piece_detector = piece_detector or TemplatePieceDetector("assets/piece_templates")
		self.position_reconstructor = position_reconstructor or PositionReconstructor(
			confidence_threshold=piece_confidence_threshold
		)
		self.side_to_move_detector = side_to_move_detector or SideToMoveDetector()
		self.position_tracker = position_tracker or PositionTracker()
		self.engine = engine or StockfishEngine()
		self.capture_interval_ms = capture_interval_ms
		self.board_confidence_threshold = board_confidence_threshold
		self.piece_confidence_threshold = piece_confidence_threshold
		self.event_callback = event_callback
		self.logger = logger or logging.getLogger(__name__)
		self.state = SEARCHING
		self._analysis_cache: dict[str, EngineAnalysis] = {}
		self._stop_event = threading.Event()
		self._worker: threading.Thread | None = None

	def start(self) -> None:
		"""Start continuous capture and analysis on a background thread."""
		if self._worker and self._worker.is_alive():
			return
		self._stop_event.clear()
		self._worker = threading.Thread(target=self._run, name="analysis-pipeline", daemon=True)
		self._worker.start()

	def stop(self) -> None:
		"""Stop the worker and release capture/engine resources when supported."""
		self._stop_event.set()
		if self._worker and self._worker is not threading.current_thread():
			self._worker.join(timeout=5)
		for resource in (self.capture, self.engine):
			close = getattr(resource, "close", None) or getattr(resource, "stop", None)
			if close:
				close()

	def process_frame(self, screen_image: Any) -> PipelineEvent:
		"""Process one captured screen image, intended for workers and integration tests."""
		try:
			board = self.board_detector.detect(screen_image)
			if board is None:
				return self._emit(PipelineEvent(SEARCHING, "Chessboard not detected"))
			if board.confidence < self.board_confidence_threshold:
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Board confidence is too low", board=board))
			self._set_state(BOARD_DETECTED)
			orientation = self.orientation_detector.detect()
			if orientation.orientation not in {"white_bottom", "black_bottom"} or orientation.confidence < 0.65:
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Board orientation is unknown", board=board))
			board = type(board)(board.x, board.y, board.width, board.height, board.square_size, board.confidence, orientation.orientation)
			squares = self.square_detector.map_squares(board)
			self._set_state(DETECTING_POSITION)
			occupancy = self.occupancy_detector.detect(screen_image, squares)
			if any(result.status == "uncertain" or result.confidence < self.piece_confidence_threshold for result in occupancy.values()):
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Square occupancy is uncertain", board=board))
			pieces = self.piece_detector.detect(screen_image, squares, occupancy)
			if not pieces or any(result.confidence < self.piece_confidence_threshold for result in pieces.values()):
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Piece recognition is uncertain", board=board))
			side = self.side_to_move_detector.detect()
			if not side.analysis_ready:
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Side to move is unknown", board=board))
			position = self.position_reconstructor.reconstruct(
				pieces,
				occupancy=occupancy,
				side_to_move=side.side_to_move,
			)
			stability = self.position_tracker.update(position)
			if not stability.stable:
				return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Waiting for stable position", board=board, position=position, stability=stability))
			if not stability.should_analyse and stability.position_hash in self._analysis_cache:
				return self._emit(PipelineEvent(ANALYSIS_READY, "Cached analysis", board=board, position=position, stability=stability, analysis=self._analysis_cache[stability.position_hash]))
			self._set_state(POSITION_STABLE)
			self._set_state(ANALYSING)
			analysis = self.engine.analyse(position.fen, depth=20, multipv=5)
			self._analysis_cache[stability.position_hash] = analysis
			return self._emit(PipelineEvent(ANALYSIS_READY, "Analysis complete", board=board, position=position, stability=stability, analysis=analysis))
		except Exception as exc:
			self.logger.exception("Analysis pipeline failed")
			return self._emit(PipelineEvent(ERROR, str(exc), error=exc))

	def _run(self) -> None:
		while not self._stop_event.is_set():
			try:
				frame = self.capture.capture()
				self.process_frame(frame)
			except Exception as exc:
				self.logger.exception("Screen capture failed")
				self._emit(PipelineEvent(ERROR, str(exc), error=exc))
			self._stop_event.wait(self.capture_interval_ms / 1000)

	def _set_state(self, state: str) -> None:
		self.state = state
		self.logger.debug("Pipeline state: %s", state)

	def _emit(self, event: PipelineEvent) -> PipelineEvent:
		self.state = event.state
		if self.event_callback:
			self.event_callback(event)
		return event
