"""Unit tests for the Phase 1 Stockfish abstraction."""

from pathlib import Path

import chess
import chess.engine
import pytest

from chess_analyser.engine import (
    EngineError,
    InvalidFENError,
    StockfishEngine,
    StockfishUnavailableError,
)


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TACTICAL_FEN = "7k/6pp/5p2/8/8/5Q2/6PP/6K1 w - - 0 1"


class FakeEngine:
    """Small deterministic stand-in for python-chess's engine protocol."""

    def __init__(self, infos):
        self.infos = infos
        self.calls = []
        self.quit_called = False

    def analyse(self, board, limit, multipv):
        self.calls.append((board.fen(), limit, multipv))
        return self.infos

    def quit(self):
        self.quit_called = True


def create_engine(tmp_path: Path, infos):
    executable = tmp_path / "stockfish"
    executable.touch()
    fake = FakeEngine(infos)
    return StockfishEngine(executable, engine_factory=lambda _path: fake), fake


def test_start_and_stop_are_clean_and_idempotent(tmp_path):
    engine, fake = create_engine(tmp_path, [])

    engine.start()
    engine.start()
    assert engine.is_running

    engine.stop()
    engine.stop()
    assert not engine.is_running
    assert fake.quit_called


def test_depth_multipv_and_centipawn_analysis(tmp_path):
    board = chess.Board(STARTING_FEN)
    infos = [
        {
            "depth": 18,
            "score": chess.engine.PovScore(chess.engine.Cp(42), chess.WHITE),
            "pv": [chess.Move.from_uci("e2e4"), chess.Move.from_uci("e7e5")],
        },
        {
            "depth": 17,
            "score": chess.engine.PovScore(chess.engine.Cp(15), chess.WHITE),
            "pv": [chess.Move.from_uci("d2d4")],
        },
    ]
    engine, fake = create_engine(tmp_path, infos)

    result = engine.analyse(STARTING_FEN, depth=18, multipv=2)

    assert result.best_move == "e2e4"
    assert result.best_move_san == "e4"
    assert result.score == pytest.approx(0.42)
    assert result.mate is None
    assert result.depth == 18
    assert len(result.lines) == 2
    assert result.lines[0].principal_variation == ["e2e4", "e7e5"]
    assert result.lines[1].san == "d4"
    assert fake.calls[0][0] == board.fen()
    assert fake.calls[0][1].depth == 18
    assert fake.calls[0][1].time is None
    assert fake.calls[0][2] == 2


def test_time_limited_analysis_forwards_seconds(tmp_path):
    infos = [
        {
            "depth": 9,
            "score": chess.engine.PovScore(chess.engine.Cp(-30), chess.WHITE),
            "pv": [chess.Move.from_uci("e2e4")],
        }
    ]
    engine, fake = create_engine(tmp_path, infos)

    result = engine.analyse(STARTING_FEN, time_ms=250, multipv=1)

    assert result.score == pytest.approx(-0.30)
    assert fake.calls[0][1].depth is None
    assert fake.calls[0][1].time == pytest.approx(0.25)


def test_mate_evaluation_is_returned_separately(tmp_path):
    infos = [
        {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE),
            "pv": [chess.Move.from_uci("f3h3")],
        }
    ]
    engine, _fake = create_engine(tmp_path, infos)

    result = engine.analyse(TACTICAL_FEN, depth=12)

    assert result.best_move == "f3h3"
    assert result.best_move_san == "Qh3"
    assert result.score is None
    assert result.mate == 3


def test_invalid_fen_is_rejected_before_starting_engine(tmp_path):
    engine, fake = create_engine(tmp_path, [])

    with pytest.raises(InvalidFENError, match="Invalid FEN"):
        engine.analyse("not a fen", depth=5)

    assert not engine.is_running
    assert not fake.quit_called


def test_missing_stockfish_has_specific_error(tmp_path):
    missing = tmp_path / "does-not-exist"
    engine = StockfishEngine(missing)

    with pytest.raises(StockfishUnavailableError, match="not found"):
        engine.start()

    assert not engine.is_running


def test_engine_failure_is_wrapped(tmp_path):
    class FailingEngine(FakeEngine):
        def analyse(self, board, limit, multipv):
            raise chess.engine.EngineError("process exited")

    executable = tmp_path / "stockfish"
    executable.touch()
    fake = FailingEngine([])
    engine = StockfishEngine(executable, engine_factory=lambda _path: fake)

    with pytest.raises(EngineError, match="analysis failed"):
        engine.analyse(STARTING_FEN, depth=5)