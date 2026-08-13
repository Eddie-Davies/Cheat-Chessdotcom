"""Compact engine evaluation panel for the transparent overlay."""

from __future__ import annotations

from dataclasses import dataclass

from chess_analyser.engine import EngineAnalysis
from chess_analyser.ui.status import format_evaluation, format_line


@dataclass(frozen=True)
class EvaluationPanelConfig:
	"""Panel placement and display settings."""

	position: str = "outside_right"
	show_alternatives: bool = True
	width: int = 170
	padding: int = 10


class EvaluationPanel:
	"""Render existing ``EngineAnalysis`` data without engine coupling."""

	_VALID_POSITIONS = {"outside_right", "outside_left", "inside_top", "inside_bottom"}

	def __init__(self, config: EvaluationPanelConfig | None = None) -> None:
		self.config = config or EvaluationPanelConfig()
		if self.config.position not in self._VALID_POSITIONS:
			raise ValueError(f"Unknown panel position: {self.config.position}")

	def lines(self, analysis: EngineAnalysis) -> list[str]:
		"""Build compact display lines for tests and non-Tk backends."""
		lines = [
			"BEST MOVE",
			analysis.best_move_san,
			format_evaluation(analysis.score, analysis.mate),
			f"Depth {analysis.depth}",
		]
		if self.config.show_alternatives and analysis.lines[1:]:
			lines.append("Alternatives")
			lines.extend(
				f"{line.san:<5} {format_line(line.score, line.mate)}"
				for line in analysis.lines[1:]
			)
		return lines

	def draw(self, canvas, board_width: int, board_height: int, analysis: EngineAnalysis) -> None:
		"""Draw the panel on a canvas using board-local coordinates."""
		canvas.delete("evaluation-panel")
		lines = self.lines(analysis)
		line_height = 18
		panel_height = self.config.padding * 2 + line_height * len(lines)
		if self.config.position == "outside_right":
			x = board_width + self.config.padding
			y = self.config.padding
		elif self.config.position == "outside_left":
			x = -self.config.width - self.config.padding
			y = self.config.padding
		elif self.config.position == "inside_bottom":
			x = self.config.padding
			y = board_height - panel_height - self.config.padding
		else:
			x = self.config.padding
			y = self.config.padding
		canvas.create_rectangle(
			x,
			y,
			x + self.config.width,
			y + panel_height,
			fill="#101820",
			outline="#49d17d",
			width=1,
			tags="evaluation-panel",
		)
		for index, line in enumerate(lines):
			canvas.create_text(
				x + self.config.padding,
				y + self.config.padding + index * line_height,
				text=line,
				anchor="nw",
				fill="#f4f7f5",
				font=("TkDefaultFont", 10, "bold" if index < 2 else "normal"),
				tags="evaluation-panel",
			)