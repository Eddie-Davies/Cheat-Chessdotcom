"""Phase 13 automatic pipeline integration tests."""

from pathlib import Path
from threading import Event
from types import SimpleNamespace

import cv2
import pytest

from chess_analyser.detection import (
	BoardDetector,
	OccupancyDetection,
	OccupancyDetector,
	OrientationDetection,
	OrientationDetector,
	SideToMoveDetection,
	SquareDetector,
	TemplatePieceDetector,
)
from chess_analyser.engine import EngineAnalysis, EngineLine
from chess_analyser.pipeline import (
	ANALYSIS_READY,
	BOARD_DETECTED,
	ERROR,
	POSITION_UNCERTAIN,
	AutomaticAnalysisPipeline,
)
from chess_analyser.pipeline.position_tracker import PositionTracker


FIXTURE = Path("assets/test_screens/chesscom_standard_start/source.png")
TEMPLATES = Path("assets/piece_templates")


class FakeOrientationDetector(OrientationDetector):
	def detect(self, **_kwargs):
		return OrientationDetection("white_bottom", 0.95, ("fixture",))


class FakeSideDetector:
	def detect(self):
		return SideToMoveDetection("white", 0.95, ("fixture",))


class FakeEngine:
	def __init__(self):
		self.calls = []

	def analyse(self, fen, *, depth, multipv, time_ms=None):
		self.calls.append((fen, depth, multipv, time_ms))
		line = EngineLine("e2e4", "e4", 0.2, None, depth, ["e2e4"])
		return EngineAnalysis("e2e4", "e4", 0.2, None, depth, [line])

	def stop(self):
		pass


class FakeCapture:
	def __init__(self, image):
		self.image = image

	def capture(self):
		return self.image

	def close(self):
		pass


def make_pipeline(image, engine, tracker=None, callback=None):
	return AutomaticAnalysisPipeline(
		capture=FakeCapture(image),
		board_detector=BoardDetector(),
		square_detector=SquareDetector(),
		orientation_detector=FakeOrientationDetector(),
		occupancy_detector=OccupancyDetector(),
		piece_detector=TemplatePieceDetector(TEMPLATES),
		position_tracker=tracker or PositionTracker(stability_frames=2),
		engine=engine,
		side_to_move_detector=FakeSideDetector(),
		event_callback=callback,
	)


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_fixture_flows_to_analysis_without_manual_fen_or_coordinates():
	image = cv2.imread(str(FIXTURE))
	engine = FakeEngine()
	pipeline = make_pipeline(image, engine)

	first = pipeline.process_frame(image)
	second = pipeline.process_frame(image)

	assert first.state == POSITION_UNCERTAIN
	assert second.state == ANALYSIS_READY
	assert second.analysis is not None
	assert second.position is not None
	assert second.position.fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
	assert len(engine.calls) == 1


@pytest.mark.standard_screen
@pytest.mark.skipif(not FIXTURE.exists(), reason="Uploaded Chess.com fixture is not available")
def test_stable_fixture_does_not_duplicate_engine_analysis():
	image = cv2.imread(str(FIXTURE))
	engine = FakeEngine()
	pipeline = make_pipeline(image, engine, tracker=PositionTracker(stability_frames=1))

	first = pipeline.process_frame(image)
	second = pipeline.process_frame(image)

	assert first.state == ANALYSIS_READY
	assert second.state == ANALYSIS_READY
	assert second.message == "Cached analysis"
	assert len(engine.calls) == 1


def test_no_board_enters_searching_state():
	class NoBoard:
		def detect(self, _image):
			return None

	pipeline = AutomaticAnalysisPipeline(capture=FakeCapture(None), board_detector=NoBoard(), engine=FakeEngine())

	event = pipeline.process_frame(None)

	assert event.state == "SEARCHING"
	assert pipeline.state == "SEARCHING"


def test_component_failure_becomes_error_event_and_callback_is_thread_safe():
	events = []
	class FailingBoard:
		def detect(self, _image):
			raise RuntimeError("fixture failure")

	pipeline = AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=FailingBoard(),
		engine=FakeEngine(),
		event_callback=events.append,
	)

	event = pipeline.process_frame(None)

	assert event.state == ERROR
	assert "fixture failure" in event.message
	assert events[-1] is event


def test_start_and_stop_run_capture_on_worker_thread():
	event_received = Event()

	class OneFrameCapture(FakeCapture):
		def capture(self):
			event_received.set()
			return self.image

	class NoBoard:
		def detect(self, _image):
			return None

	pipeline = AutomaticAnalysisPipeline(
		capture=OneFrameCapture(None),
		board_detector=NoBoard(),
		engine=FakeEngine(),
		capture_interval_ms=0,
	)

	pipeline.start()
	assert event_received.wait(timeout=2)
	pipeline.stop()

	assert pipeline.state == "SEARCHING"
	assert pipeline._worker is not None
	assert not pipeline._worker.is_alive()


def test_confident_board_bounds_are_cached_between_refreshes():
	class CountingBoardDetector:
		def __init__(self):
			self.calls = 0

		def detect(self, _image):
			self.calls += 1
			return SimpleNamespace(
				x=10,
				y=20,
				width=800,
				height=800,
				square_size=100.0,
				confidence=0.60,
				orientation="unknown",
			)

	detector = CountingBoardDetector()
	pipeline = AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=detector,
		engine=FakeEngine(),
		board_detection_interval_ms=10_000,
	)

	first = pipeline._get_board(None)
	second = pipeline._get_board(None)

	assert first is second
	assert detector.calls == 1


def test_tiny_redetection_is_ignored_in_favor_of_cached_board():
	class SwitchingBoardDetector:
		def __init__(self):
			self.calls = 0

		def detect(self, _image):
			self.calls += 1
			if self.calls == 1:
				return SimpleNamespace(x=10, y=20, width=900, height=900, square_size=112.5, confidence=0.6, orientation="unknown")
			return SimpleNamespace(x=1000, y=900, width=120, height=120, square_size=15.0, confidence=0.6, orientation="unknown")

	pipeline = AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=SwitchingBoardDetector(),
		engine=FakeEngine(),
		board_detection_interval_ms=0,
	)

	first = pipeline._get_board(None)
	second = pipeline._get_board(None)

	assert first.width == 900
	assert second is first


def test_confidently_stronger_resize_is_still_trusted():
	class SwitchingBoardDetector:
		def __init__(self):
			self.calls = 0

		def detect(self, _image):
			self.calls += 1
			if self.calls == 1:
				return SimpleNamespace(x=10, y=20, width=900, height=900, square_size=112.5, confidence=0.6, orientation="unknown")
			return SimpleNamespace(x=1000, y=900, width=120, height=120, square_size=15.0, confidence=0.95, orientation="unknown")

	pipeline = AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=SwitchingBoardDetector(),
		engine=FakeEngine(),
		board_detection_interval_ms=0,
	)

	pipeline._get_board(None)
	second = pipeline._get_board(None)

	assert second.width == 120


def _make_squares_pipeline(occupancy_detector, piece_detector):
	class FakeBoardDetector:
		def detect(self, _image):
			return _board_detection()

	return AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=FakeBoardDetector(),
		orientation_detector=FakeOrientationDetector(),
		occupancy_detector=occupancy_detector,
		piece_detector=piece_detector,
		engine=FakeEngine(),
	)


def _board_detection():
	from chess_analyser.detection import BoardDetection

	return BoardDetection(0, 0, 800, 800, 100.0, 0.9, "unknown")


def test_a_few_uncertain_squares_are_treated_as_empty_instead_of_blocking():
	class OneUncertainOccupancy:
		def detect(self, _image, squares):
			return {
				name: OccupancyDetection(name, "uncertain", 0.3, 0.1, 0.05)
				if name == "d1"
				else OccupancyDetection(name, "empty", 0.9, 0.0, 0.0)
				for name in squares
			}

	class NoPieceDetector:
		def detect(self, _image, _squares, _occupancy):
			return {}

	pipeline = _make_squares_pipeline(OneUncertainOccupancy(), NoPieceDetector())

	event = pipeline.process_frame(None)

	assert event.state == POSITION_UNCERTAIN
	assert "Piece recognition is uncertain" in event.message


def test_many_uncertain_squares_still_block_analysis():
	class ManyUncertainOccupancy:
		def detect(self, _image, squares):
			uncertain = {"a4", "a5", "b4", "b5", "c4"}
			return {
				name: OccupancyDetection(name, "uncertain", 0.3, 0.1, 0.05)
				if name in uncertain
				else OccupancyDetection(name, "empty", 0.9, 0.0, 0.0)
				for name in squares
			}

	class NoPieceDetector:
		def detect(self, _image, _squares, _occupancy):
			return {}

	pipeline = _make_squares_pipeline(ManyUncertainOccupancy(), NoPieceDetector())

	event = pipeline.process_frame(None)

	assert event.state == POSITION_UNCERTAIN
	assert "Square occupancy is uncertain" in event.message


def test_manual_calibration_skips_board_and_orientation_detection():
	class FailingBoardDetector:
		def detect(self, _image):
			raise AssertionError("automatic board detection should be bypassed")

	class FailingOrientationDetector:
		def detect(self, **_kwargs):
			raise AssertionError("automatic orientation detection should be bypassed")

	class EmptyOccupancy:
		def detect(self, _image, squares):
			return {name: OccupancyDetection(name, "empty", 0.9, 0.0, 0.0) for name in squares}

	class NoPieceDetector:
		def detect(self, _image, _squares, _occupancy):
			return {}

	pipeline = AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=FailingBoardDetector(),
		orientation_detector=FailingOrientationDetector(),
		occupancy_detector=EmptyOccupancy(),
		piece_detector=NoPieceDetector(),
		engine=FakeEngine(),
	)
	pipeline.set_manual_calibration(x=10, y=20, width=800, height=800, orientation="black_bottom")

	event = pipeline.process_frame(None)

	assert event.state != ERROR
	assert event.board.orientation == "black_bottom"
	assert event.board.confidence == 1.0


def test_clear_manual_calibration_restores_automatic_detection():
	pipeline = AutomaticAnalysisPipeline(capture=FakeCapture(None), board_detector=None, engine=FakeEngine())
	pipeline.set_manual_calibration(x=0, y=0, width=800, height=800, orientation="white_bottom")

	pipeline.clear_manual_calibration()

	assert pipeline._manual_board is None
	assert pipeline._manual_orientation is None


class _FixedPositionOccupancy:
	def __init__(self, pieces):
		self.pieces = pieces

	def detect(self, _image, squares):
		return {
			name: OccupancyDetection(name, "occupied", 0.95, 0.5, 0.3)
			if name in self.pieces
			else OccupancyDetection(name, "empty", 0.95, 0.0, 0.0)
			for name in squares
		}


class _FixedPositionPieces:
	def __init__(self, pieces):
		self.pieces = pieces

	def detect(self, _image, _squares, _occupancy):
		from chess_analyser.detection import PieceDetection

		return {name: PieceDetection(name, piece, 0.95) for name, piece in self.pieces.items()}


class _UnknownClockDetector:
	"""Simulates a game with no visible clock at all (e.g. correspondence)."""

	def detect(self, _image, _board):
		from chess_analyser.detection import ClockSignal

		return ClockSignal("unknown", 0.0, 0.0)


def _make_position_pipeline(pieces, *, stability_frames=1):
	class FixedBoardDetector:
		def detect(self, _image):
			return _board_detection()

	return AutomaticAnalysisPipeline(
		capture=FakeCapture(None),
		board_detector=FixedBoardDetector(),
		orientation_detector=FakeOrientationDetector(),
		occupancy_detector=_FixedPositionOccupancy(pieces),
		piece_detector=_FixedPositionPieces(pieces),
		clock_detector=_UnknownClockDetector(),
		position_tracker=PositionTracker(stability_frames=stability_frames),
		engine=FakeEngine(),
	)


def test_starting_position_infers_white_to_move_without_any_clock_signal():
	from chess_analyser.pipeline.analyser import _STANDARD_STARTING_PLACEMENT

	pipeline = _make_position_pipeline(_STANDARD_STARTING_PLACEMENT)

	event = pipeline.process_frame(None)

	assert event.state == ANALYSIS_READY
	assert event.position.side_to_move == "white"


def test_side_to_move_alternates_after_confirmed_change_without_clock():
	from chess_analyser.pipeline.analyser import _STANDARD_STARTING_PLACEMENT

	starting = dict(_STANDARD_STARTING_PLACEMENT)
	pipeline = _make_position_pipeline(starting)
	first = pipeline.process_frame(None)
	assert first.position.side_to_move == "white"

	after_e4 = dict(starting)
	del after_e4["e2"]
	after_e4["e4"] = "white_pawn"
	pipeline.occupancy_detector = _FixedPositionOccupancy(after_e4)
	pipeline.piece_detector = _FixedPositionPieces(after_e4)

	second = pipeline.process_frame(None)

	assert second.state == ANALYSIS_READY
	assert second.position.side_to_move == "black"


def test_confirm_current_side_to_move_bootstraps_a_clockless_midgame_position():
	from chess_analyser.pipeline.analyser import _STANDARD_STARTING_PLACEMENT

	midgame = dict(_STANDARD_STARTING_PLACEMENT)
	del midgame["e2"]
	midgame["e4"] = "white_pawn"
	pipeline = _make_position_pipeline(midgame)

	uncertain = pipeline.process_frame(None)
	assert uncertain.state == POSITION_UNCERTAIN
	assert "Side to move" in uncertain.message

	assert pipeline.confirm_current_side_to_move("black") is True

	resolved = pipeline.process_frame(None)
	assert resolved.state == ANALYSIS_READY
	assert resolved.position.side_to_move == "black"


def test_confirm_current_side_to_move_returns_false_before_any_frame_processed():
	pipeline = AutomaticAnalysisPipeline(capture=FakeCapture(None), board_detector=None, engine=FakeEngine())

	assert pipeline.confirm_current_side_to_move("white") is False


def test_confirm_current_side_to_move_rejects_invalid_side():
	pipeline = AutomaticAnalysisPipeline(capture=FakeCapture(None), board_detector=None, engine=FakeEngine())

	with pytest.raises(ValueError):
		pipeline.confirm_current_side_to_move("purple")