"""Real Stockfish integration smoke test."""

from pathlib import Path

import pytest

from chess_analyser.engine import StockfishEngine


ENGINE_PATH = Path("engine/stockfish/windows/stockfish.exe")
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@pytest.mark.integration
def test_real_stockfish_startup_and_analysis():
	if not ENGINE_PATH.exists():
		pytest.skip("Windows Stockfish executable is not installed")

	engine = StockfishEngine(ENGINE_PATH)
	try:
		result = engine.analyse(STARTING_FEN, depth=8, multipv=3)
	finally:
		engine.stop()

	assert result.best_move
	assert result.best_move_san
	assert result.depth >= 1
	assert len(result.lines) == 3