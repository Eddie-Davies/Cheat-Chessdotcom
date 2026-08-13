"""Phase 16 evaluation panel tests."""

import pytest

from chess_analyser.engine import EngineAnalysis, EngineLine
from chess_analyser.overlay import EvaluationPanel, EvaluationPanelConfig


def analysis():
	return EngineAnalysis(
		best_move="e2e4",
		best_move_san="e4",
		score=0.42,
		mate=None,
		depth=20,
		lines=[
			EngineLine("e2e4", "e4", 0.42, None, 20, ["e2e4"]),
			EngineLine("d2d4", "d4", 0.35, None, 19, ["d2d4"]),
			EngineLine("g1f3", "Nf3", 0.28, None, 18, ["g1f3"]),
		],
	)


def test_panel_lines_show_best_move_evaluation_depth_and_alternatives():
	lines = EvaluationPanel().lines(analysis())

	assert lines[:4] == ["BEST MOVE", "e4", "+0.42", "Depth 20"]
	assert lines[4:] == ["Alternatives", "d4    +0.35", "Nf3   +0.28"]


def test_panel_can_hide_alternatives():
	lines = EvaluationPanel(EvaluationPanelConfig(show_alternatives=False)).lines(analysis())

	assert lines == ["BEST MOVE", "e4", "+0.42", "Depth 20"]


def test_mate_evaluation_is_displayed():
	mate_analysis = EngineAnalysis(
		best_move="f7f8q",
		best_move_san="Qxf8#",
		score=None,
		mate=1,
		depth=25,
		lines=[],
	)

	assert EvaluationPanel().lines(mate_analysis)[2] == "Mate in 1"


def test_panel_positions_are_configurable_and_validated():
	for position in ("outside_right", "outside_left", "inside_top", "inside_bottom"):
		assert EvaluationPanel(EvaluationPanelConfig(position=position)).config.position == position
	with pytest.raises(ValueError):
		EvaluationPanel(EvaluationPanelConfig(position="invalid"))


class FakeCanvas:
	def __init__(self):
		self.calls = []

	def delete(self, tag):
		self.calls.append(("delete", tag))

	def create_rectangle(self, *args, **kwargs):
		self.calls.append(("rectangle", args, kwargs))

	def create_text(self, *args, **kwargs):
		self.calls.append(("text", args, kwargs))


def test_panel_draws_compact_canvas_annotations_outside_board():
	canvas = FakeCanvas()
	EvaluationPanel().draw(canvas, 928, 928, analysis())

	assert canvas.calls[0] == ("delete", "evaluation-panel")
	rectangle = next(call for call in canvas.calls if call[0] == "rectangle")
	assert rectangle[1][0] > 928
	assert any(call[0] == "text" and call[2]["text"] == "BEST MOVE" for call in canvas.calls)