"""Phase 13 automatic pipeline integration tests."""

from pathlib import Path
from threading import Event
from types import SimpleNamespace

import cv2
import pytest

from chess_analyser.detection import (
	BoardDetector,
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