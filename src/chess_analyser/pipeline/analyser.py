"""Asynchronous automatic screen-to-analysis pipeline."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from chess_analyser.chess import PositionDetection, PositionReconstructor
from chess_analyser.detection import (
	BoardDetection,
	BoardDetector,
	ChessComClockDetector,
	OccupancyDetector,
	OrientationDetection,
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

# White always moves first, so a detected starting arrangement resolves the
# side to move by chess rules rather than a site-specific UI heuristic.
_STANDARD_STARTING_PLACEMENT = {
	"a1": "white_rook", "b1": "white_knight", "c1": "white_bishop", "d1": "white_queen",
	"e1": "white_king", "f1": "white_bishop", "g1": "white_knight", "h1": "white_rook",
	"a2": "white_pawn", "b2": "white_pawn", "c2": "white_pawn", "d2": "white_pawn",
	"e2": "white_pawn", "f2": "white_pawn", "g2": "white_pawn", "h2": "white_pawn",
	"a7": "black_pawn", "b7": "black_pawn", "c7": "black_pawn", "d7": "black_pawn",
	"e7": "black_pawn", "f7": "black_pawn", "g7": "black_pawn", "h7": "black_pawn",
	"a8": "black_rook", "b8": "black_knight", "c8": "black_bishop", "d8": "black_queen",
	"e8": "black_king", "f8": "black_bishop", "g8": "black_knight", "h8": "black_rook",
}


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
		clock_detector: Any | None = None,
		capture_interval_ms: int = 100,
		board_detection_interval_ms: int = 5000,
		board_confidence_threshold: float = 0.58,
		piece_confidence_threshold: float = 0.45,
		engine_depth: int = 20,
		engine_time_ms: int | None = None,
		engine_multipv: int = 5,
		event_callback: Callable[[PipelineEvent], None] | None = None,
		logger: logging.Logger | None = None,
	) -> None:
		if capture_interval_ms < 0:
			raise ValueError("capture_interval_ms must not be negative")
		if board_detection_interval_ms < 0:
			raise ValueError("board_detection_interval_ms must not be negative")
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
		self.clock_detector = clock_detector or ChessComClockDetector()
		self.position_tracker = position_tracker or PositionTracker()
		self.engine = engine or StockfishEngine()
		self.capture_interval_ms = capture_interval_ms
		self.board_detection_interval_ms = board_detection_interval_ms
		self.board_confidence_threshold = board_confidence_threshold
		self.piece_confidence_threshold = piece_confidence_threshold
		self.engine_depth = engine_depth
		self.engine_time_ms = engine_time_ms
		self.engine_multipv = engine_multipv
		self.event_callback = event_callback
		self.logger = logger or logging.getLogger(__name__)
		self.state = SEARCHING
		self._analysis_cache: dict[str, EngineAnalysis] = {}
		self._stop_event = threading.Event()
		self._worker: threading.Thread | None = None
		self._cached_board: Any | None = None
		self._last_board_detection_at = 0.0
		self._cached_orientation: Any | None = None
		self._manual_board: BoardDetection | None = None
		self._manual_orientation: str | None = None
		self._last_committed_placement: dict[str, str] | None = None
		self._last_committed_side: str | None = None
		self._last_seen_placement: dict[str, str] | None = None

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
		self._cached_board = None
		self._last_board_detection_at = 0.0
		self._cached_orientation = None
		self._last_committed_placement = None
		self._last_committed_side = None
		self._last_seen_placement = None

	def set_manual_calibration(self, *, x: int, y: int, width: int, height: int, orientation: str) -> None:
		"""Pin board bounds and orientation from user-verified calibration, bypassing detection."""
		if orientation not in {"white_bottom", "black_bottom"}:
			raise ValueError("orientation must be 'white_bottom' or 'black_bottom'")
		self._manual_board = BoardDetection(x, y, width, height, width / 8, 1.0, orientation)
		self._manual_orientation = orientation
		self._cached_board = None
		self._cached_orientation = None
		self._last_committed_placement = None
		self._last_committed_side = None

	def clear_manual_calibration(self) -> None:
		"""Return to automatic board and orientation detection."""
		self._manual_board = None
		self._manual_orientation = None
		self._last_committed_placement = None
		self._last_committed_side = None

	def confirm_current_side_to_move(self, side: str) -> bool:
		"""Manually seed whose turn it is right now, e.g. via a user hotkey.

		This is a documented fallback (see AGENTS.md 3.5) for games with no
		visible clock/turn indicator at all (correspondence games) where the
		automatic starting-position/alternation inference has no reference point
		to bootstrap from. After this call, subsequent confirmed position changes
		continue to alternate automatically; no further manual input is needed.
		Returns False if no piece placement has been recognised yet.
		"""
		if side not in {"white", "black"}:
			raise ValueError("side must be 'white' or 'black'")
		if self._last_seen_placement is None:
			return False
		self._last_committed_placement = self._last_seen_placement
		self._last_committed_side = side
		return True

	def process_frame(self, screen_image: Any) -> PipelineEvent:
		"""Process one captured screen image, intended for workers and integration tests."""
		try:
			if self._manual_board is not None:
				board = self._manual_board
			else:
				board = self._get_board(screen_image)
				if board is None:
					return self._emit(PipelineEvent(SEARCHING, "Chessboard not detected"))
				if board.confidence < self.board_confidence_threshold:
					return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Board confidence is too low", board=board))
			self._set_state(BOARD_DETECTED)
			if self._manual_orientation is not None:
				orientation = OrientationDetection(self._manual_orientation, 1.0, ("manual_calibration",))
			else:
				orientation = self._get_orientation(screen_image, board)
				if orientation.orientation not in {"white_bottom", "black_bottom"} or orientation.confidence < 0.65:
					return self._emit(PipelineEvent(POSITION_UNCERTAIN, "Board orientation is unknown", board=board))
			board = type(board)(board.x, board.y, board.width, board.height, board.square_size, board.confidence, orientation.orientation)
			squares = self.square_detector.map_squares(board)
			self._set_state(DETECTING_POSITION)
			occupancy = self.occupancy_detector.detect(screen_image, squares)
			# Empty squares rarely reach the piece-confidence threshold and do not
			# need to; only a shaky "occupied" call should block on its own.
			# A handful of "uncertain" squares (highlight/annotation artifacts) are
			# treated as empty instead of blocking the whole frame; python-chess
			# validation below still rejects positions that come out illegal.
			uncertain_squares = sorted(name for name, result in occupancy.items() if result.status == "uncertain")
			low_confidence_occupied = sorted(
				name for name, result in occupancy.items()
				if result.status == "occupied" and result.confidence < self.piece_confidence_threshold
			)
			if len(uncertain_squares) > 4 or low_confidence_occupied:
				blocking_squares = uncertain_squares + low_confidence_occupied
				shown = ", ".join(sorted(blocking_squares)[:8])
				return self._emit(
					PipelineEvent(
						POSITION_UNCERTAIN,
						f"Square occupancy is uncertain at {shown}",
						board=board,
					)
				)
			occupancy = {name: result for name, result in occupancy.items() if name not in uncertain_squares}
			pieces = self.piece_detector.detect(screen_image, squares, occupancy)
			low_confidence_pieces = sorted(
				name for name, result in pieces.items() if result.confidence < self.piece_confidence_threshold
			)
			if not pieces or low_confidence_pieces:
				shown = ", ".join(low_confidence_pieces[:8]) or "no pieces recognised"
				return self._emit(
					PipelineEvent(POSITION_UNCERTAIN, f"Piece recognition is uncertain at {shown}", board=board)
				)
			clock = self.clock_detector.detect(screen_image, board)
			player_bottom = "white" if orientation.orientation == "white_bottom" else "black"
			if clock.side == "bottom":
				active_player = player_bottom
			elif clock.side == "top":
				active_player = "black" if player_bottom == "white" else "white"
			else:
				# clock.side == "unknown": no reliable clock signal at all, so
				# this must not masquerade as a confident active-player vote.
				active_player = None
			placement = {name: result.piece for name, result in pieces.items()}
			self._last_seen_placement = placement
			inferred_side = self._infer_side_from_history(placement)
			side = self._detect_side_to_move(
				active_player=active_player,
				clock_side=clock.side,
				confirmed_history=[inferred_side] if inferred_side else None,
			)
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
			# Remember this confirmed placement/side so the next stable change
			# can be resolved by alternation even without a clock/UI signal.
			self._last_committed_placement = placement
			self._last_committed_side = side.side_to_move
			if not stability.should_analyse and stability.position_hash in self._analysis_cache:
				return self._emit(PipelineEvent(ANALYSIS_READY, "Cached analysis", board=board, position=position, stability=stability, analysis=self._analysis_cache[stability.position_hash]))
			self._set_state(POSITION_STABLE)
			self._set_state(ANALYSING)
			analysis = self.engine.analyse(
				position.fen,
				depth=self.engine_depth,
				time_ms=self.engine_time_ms,
				multipv=self.engine_multipv,
			)
			self._analysis_cache[stability.position_hash] = analysis
			return self._emit(PipelineEvent(ANALYSIS_READY, "Analysis complete", board=board, position=position, stability=stability, analysis=analysis))
		except Exception as exc:
			self.logger.exception("Analysis pipeline failed")
			return self._emit(PipelineEvent(ERROR, str(exc), error=exc))

	def _detect_orientation_from_screen(self, image: Any, board: Any) -> Any:
		"""Read only the four corner squares; scanning all 64 here would double
		the per-frame occupancy/piece detection cost for no extra evidence."""
		provisional = type(board)(board.x, board.y, board.width, board.height, board.square_size, board.confidence, "white_bottom")
		all_squares = self.square_detector.map_squares(provisional)
		corner_names = {"top_left": "a8", "top_right": "h8", "bottom_left": "a1", "bottom_right": "h1"}
		corner_squares = {name: all_squares[name] for name in corner_names.values()}
		occupancy = self.occupancy_detector.detect(image, corner_squares)
		pieces = self.piece_detector.detect(image, corner_squares, occupancy)
		corner_pieces = {
			corner: pieces[name].piece
			for corner, name in corner_names.items()
			if name in pieces and pieces[name].piece != "unknown"
		}
		return self.orientation_detector.detect(corner_pieces=corner_pieces)

	def _get_orientation(self, image: Any, board: Any) -> Any:
		if self._cached_orientation is not None:
			return self._cached_orientation
		orientation = self._detect_orientation_from_screen(image, board)
		if orientation.orientation in {"white_bottom", "black_bottom"} and orientation.confidence >= 0.65:
			self._cached_orientation = orientation
		return orientation

	def _get_board(self, screen_image: Any) -> Any | None:
		now = time.monotonic()
		cache_is_fresh = (
			self._cached_board is not None
			and (
				self.board_detection_interval_ms == 0
				or now - self._last_board_detection_at >= self.board_detection_interval_ms / 1000
			)
		)
		if self._cached_board is not None and not cache_is_fresh:
			return self._cached_board
		board = self.board_detector.detect(screen_image)
		self._last_board_detection_at = now
		if board is not None and self._cached_board is not None and self._is_implausible_resize(board):
			# A tiny/oversized candidate relative to a previously trusted board is
			# more likely a stray UI element than the real board shrinking; keep
			# the established bounds instead of latching onto noise.
			self.logger.debug(
				"Ignoring implausible board resize %dx%d vs cached %dx%d",
				board.width,
				board.height,
				self._cached_board.width,
				self._cached_board.height,
			)
			return self._cached_board
		if board is not None and board.confidence >= self.board_confidence_threshold:
			self._cached_board = board
			self.logger.info(
				"Caching board bounds at (%d, %d) size %dx%d confidence %.3f",
				board.x,
				board.y,
				board.width,
				board.height,
				board.confidence,
			)
		elif board is None:
			self._cached_board = None
			self._cached_orientation = None
			self._last_committed_placement = None
			self._last_committed_side = None
			self._last_seen_placement = None
		else:
			# A fresh detection below threshold invalidates any orientation cached
			# for the previous board so it is not reused against different geometry.
			self._cached_orientation = None
		return board

	def _is_implausible_resize(self, board: Any) -> bool:
		"""Reject a re-detection that shrank/grew drastically without a clearly
		stronger confidence; that pattern matches noise more than a real board resize."""
		cached = self._cached_board
		if cached is None:
			return False
		size_ratio = board.width / cached.width if cached.width else 1.0
		drastic_change = size_ratio < 0.6 or size_ratio > 1.67
		clearly_stronger = board.confidence >= cached.confidence + 0.1
		return drastic_change and not clearly_stronger

	def _detect_side_to_move(self, *, active_player: str | None, clock_side: str, confirmed_history: list[str] | None = None) -> Any:
		active_clock = active_player if clock_side in {"top", "bottom"} else None
		try:
			return self.side_to_move_detector.detect(
				active_player=active_player,
				active_clock=active_clock,
				confirmed_history=confirmed_history,
			)
		except TypeError:
			return self.side_to_move_detector.detect()

	def _infer_side_from_history(self, placement: dict[str, str]) -> str | None:
		"""Infer whose turn it is without a clock/UI signal (e.g. correspondence
		games with no running clock): the starting position is always White's
		turn by chess rules, and turns alternate on every confirmed change after
		that, so no site-specific heuristic is required."""
		if placement == _STANDARD_STARTING_PLACEMENT:
			return "white"
		if placement == self._last_committed_placement:
			return self._last_committed_side
		if self._last_committed_side is not None:
			return "black" if self._last_committed_side == "white" else "white"
		return None

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
		self.logger.info(
			"Pipeline event state=%s message=%s board_confidence=%s pieces=%s",
			event.state,
			event.message or "-",
			f"{event.board.confidence:.3f}" if event.board is not None else "-",
			len(event.position.pieces) if event.position is not None else "-",
		)
		if self.event_callback:
			self.event_callback(event)
		return event
