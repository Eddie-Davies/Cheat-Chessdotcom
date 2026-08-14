"""Unit tests for the minimal Chess Analyser control window."""

import tkinter as tk

import pytest

from chess_analyser.engine import EngineAnalysis, EngineLine
from chess_analyser.pipeline import PipelineEvent
from chess_analyser.ui import MainWindow, format_evaluation


class FakeEngine:
    def __init__(self):
        self.calls = []
        self.stopped = False

    def analyse(self, fen, *, depth, time_ms, multipv):
        self.calls.append((fen, depth, time_ms, multipv))
        return EngineAnalysis(
            best_move="e2e4",
            best_move_san="e4",
            score=0.42,
            mate=None,
            depth=depth,
            lines=[
                EngineLine("e2e4", "e4", 0.42, None, depth, ["e2e4", "e7e5"]),
                EngineLine("d2d4", "d4", 0.31, None, depth, ["d2d4"]),
            ],
        )

    def stop(self):
        self.stopped = True


class FakePipeline:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.event_callback = None

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def create_window_or_skip(engine, **kwargs):
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tkinter display unavailable: {exc}")
    root.withdraw()
    return root, MainWindow(root, engine=engine, **kwargs)


def test_status_formatting():
    assert format_evaluation(0.42, None) == "+0.42"
    assert format_evaluation(-0.3, None) == "-0.30"
    assert format_evaluation(None, 3) == "Mate in 3"
    assert format_evaluation(None, -2) == "Mate in 2 (black)"


def test_window_only_exposes_start_and_detect_board_buttons():
    engine = FakeEngine()
    root, window = create_window_or_skip(engine)
    try:
        assert window.start_button["text"] == "Start"
        assert window.calibrate_button["text"] == "Detect Board"
        assert not hasattr(window, "analyse_button")
        assert not hasattr(window, "alternatives")
        assert not hasattr(window, "settings_button")
    finally:
        window.close()


def test_start_stop_toggles_pipeline_lifecycle():
    engine = FakeEngine()
    pipeline = FakePipeline()
    root, window = create_window_or_skip(engine, pipeline=pipeline)
    try:
        window.start()
        assert pipeline.started
        assert window.start_button["text"] == "Stop"

        window.pause()
        assert pipeline.stopped
        assert window.start_button["text"] == "Start"
        assert window.pipeline is None
    finally:
        window.close()


def test_analysis_ready_event_updates_status_without_removed_widgets():
    engine = FakeEngine()
    root, window = create_window_or_skip(engine)
    try:
        analysis = engine.analyse("startpos", depth=10, time_ms=None, multipv=2)
        event = PipelineEvent("ANALYSIS_READY", "Analysis complete", board=None, analysis=None)
        window._apply_pipeline_event(event)
        assert window.status_var.get() == "Analysis complete"
        assert analysis.best_move_san == "e4"
    finally:
        window.close()


def test_close_stops_engine_when_no_pipeline():
    engine = FakeEngine()
    root, window = create_window_or_skip(engine)
    window.close()
    assert engine.stopped
