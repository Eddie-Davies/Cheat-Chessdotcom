"""Tests for Phase 11 side-to-move detection."""

import pytest

from chess_analyser.chess import PositionReconstructor, UnknownSideToMoveError
from chess_analyser.detection import SideToMoveDetector


def test_white_side_from_active_player_and_highlight():
	result = SideToMoveDetector().detect(active_player="white", board_highlight="white")

	assert result.side_to_move == "white"
	assert result.confidence > 0.8
	assert result.analysis_ready


def test_black_side_from_ui_indicator_and_clock():
	result = SideToMoveDetector().detect(ui_indicator="black", active_clock="black")

	assert result.side_to_move == "black"
	assert result.confidence > 0.8
	assert result.analysis_ready


def test_confirmed_history_can_supply_side_when_current_ui_signal_is_missing():
	result = SideToMoveDetector().detect(confirmed_history=["white", "black"])

	assert result.side_to_move == "black"
	assert result.confidence >= 0.65
	assert "history:black" in result.signals


def test_conflicting_signals_return_unknown():
	result = SideToMoveDetector().detect(active_player="white", board_highlight="black")

	assert result.side_to_move == "unknown"
	assert result.confidence == 0.5
	assert not result.analysis_ready


def test_missing_signals_return_unknown():
	result = SideToMoveDetector().detect()

	assert result.side_to_move == "unknown"
	assert result.confidence == 0.0
	assert not result.analysis_ready


def test_reconstruction_rejects_unknown_side_to_move():
	with pytest.raises(UnknownSideToMoveError, match="Side to move is unknown"):
		PositionReconstructor().reconstruct({"e1": "white_king", "e8": "black_king"})