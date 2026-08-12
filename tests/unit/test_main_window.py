"""Unit tests for the Phase 3 Tkinter interface."""

import time
import tkinter as tk

import chess
import pytest

from chess_analyser.engine import EngineAnalysis, EngineLine
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


def create_window_or_skip(engine):
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tkinter display unavailable: {exc}")
    root.withdraw()
    return root, MainWindow(root, engine=engine)


def test_status_formatting():
    assert format_evaluation(0.42, None) == "+0.42"
    assert format_evaluation(-0.3, None) == "-0.30"
    assert format_evaluation(None, 3) == "Mate in 3"
    assert format_evaluation(None, -2) == "Mate in 2 (black)"


def test_fen_analysis_updates_ui_without_blocking_main_thread():
    engine = FakeEngine()
    root, window = create_window_or_skip(engine)
    try:
        window.depth_var.set("12")
        window.time_var.set("0.25")
        window.multipv_var.set("2")
        window.fen_var.set("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

        window.analyse_button.invoke()
        assert window._worker is not None

        deadline = time.monotonic() + 2
        while window.status_var.get() != "Analysis complete" and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)

        assert window.status_var.get() == "Analysis complete"
        assert window.best_move_var.get() == "e4"
        assert window.evaluation_var.get() == "+0.42"
        assert window.depth_display_var.get() == "12"
        assert window.alternatives.get(0) == "d4  +0.31  (depth 12)"
        assert engine.calls == [(window.fen_var.get(), 12, 250, 2)]
    finally:
        window.close()
        assert engine.stopped


def test_invalid_fen_does_not_start_worker():
    engine = FakeEngine()
    root, window = create_window_or_skip(engine)
    try:
        window.fen_var.set("not a fen")
        window._on_analyse()

        assert window.status_var.get().startswith("Invalid analysis input:")
        assert not engine.calls
        assert str(window.analyse_button["state"]) == "normal"
    finally:
        window.close()