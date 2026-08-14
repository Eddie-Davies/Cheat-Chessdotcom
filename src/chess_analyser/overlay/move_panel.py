"""Side-docked move-instruction panel that never draws over the captured board.

Unlike the on-board arrow overlay, this panel is a separate window pinned to
the right edge of the screen. It never overlaps the chessboard region, so it
cannot appear in the next screen capture and confuse board/piece detection.
"""

from __future__ import annotations

import time
import tkinter as tk
from typing import Any

import chess

from chess_analyser.chess import PositionDetection
from chess_analyser.engine import EngineAnalysis
from chess_analyser.ui.status import format_evaluation, format_line

from .hotkeys import GlobalHotkeyService, HotkeyStatus, OverlayVisibilityController


def describe_move(pieces: dict[str, str] | None, uci_move: str) -> str:
	"""Return a plain-language instruction for a UCI move, e.g. "Move white knight from g1 to f3"."""
	try:
		move = chess.Move.from_uci(uci_move)
	except ValueError:
		return f"Play {uci_move}"
	source = chess.square_name(move.from_square)
	destination = chess.square_name(move.to_square)
	piece_value = (pieces or {}).get(source)
	piece_label = piece_value.replace("_", " ") if piece_value else "piece"
	instruction = f"Move {piece_label} from {source} to {destination}"
	if move.promotion:
		instruction += f", promoting to {chess.piece_name(move.promotion)}"
	return instruction


class MovePanel:
	"""Borderless, always-on-top text panel docked to the right screen edge."""

	def __init__(
		self,
		root: tk.Misc | None = None,
		*,
		width: int = 300,
		height: int = 220,
		hotkey_service: GlobalHotkeyService | None = None,
	) -> None:
		if width < 200:
			raise ValueError("width must be at least 200")
		if height < 120:
			raise ValueError("height must be at least 120")
		self._owns_root = root is None
		self.root = root or tk.Tk()
		self.window = self.root if root is None else tk.Toplevel(root)
		self.width = width
		self.height = height
		self.visible = False
		self._last_message: str | None = None
		self.hotkey_service = hotkey_service
		self.visibility_controller = OverlayVisibilityController(
			self,
			dispatch=lambda callback: self.root.after(0, callback),
		)
		self.window.title("Chess Analyser - Move Assistant")
		self.window.attributes("-topmost", True)
		self._position_window()
		self.text = tk.Text(
			self.window,
			wrap="word",
			state="disabled",
			bg="#101820",
			fg="#eafff2",
			insertbackground="#eafff2",
			padx=12,
			pady=12,
			font=("TkDefaultFont", 11),
		)
		self.text.pack(fill="both", expand=True)
		self.window.protocol("WM_DELETE_WINDOW", self.close)
		self.window.withdraw()

	def _position_window(self) -> None:
		screen_width = self.window.winfo_screenwidth()
		x = max(0, screen_width - self.width - 10)
		self.window.geometry(f"{self.width}x{self.height}+{x}+40")

	def show(self) -> None:
		self.window.deiconify()
		self.window.attributes("-topmost", True)
		self.visible = True

	def hide(self) -> None:
		self.window.withdraw()
		self.visible = False

	def start_hotkey(self, service: GlobalHotkeyService | None = None) -> HotkeyStatus:
		"""Register the configured global toggle key and return its status."""
		self.hotkey_service = service or self.hotkey_service or GlobalHotkeyService()
		return self.hotkey_service.start(self.visibility_controller.toggle)

	def stop_hotkey(self) -> None:
		if self.hotkey_service:
			self.hotkey_service.stop()

	def update(
		self,
		board: Any | None = None,
		best_move: str | None = None,
		analysis: EngineAnalysis | None = None,
		*,
		position: PositionDetection | None = None,
	) -> None:
		"""Replace the panel with only the latest instruction; ignores board geometry.

		Visibility is controlled solely by show()/hide() (the F8 hotkey), so a
		new move never pops the panel back up after the user has hidden it.
		"""
		del board  # The panel never aligns to the board, so geometry is unused.
		message = self._format_message(best_move, analysis, position)
		if not message or message == self._last_message:
			return
		self._last_message = message
		self._set_content(message)

	def set_status(self, message: str) -> None:
		"""Replace the panel with a plain status line, e.g. waiting-for-board messages."""
		if message == self._last_message:
			return
		self._last_message = message
		self._set_content(message)

	@staticmethod
	def _format_message(
		best_move: str | None,
		analysis: EngineAnalysis | None,
		position: PositionDetection | None,
	) -> str:
		if analysis is None:
			return ""
		lines = [format_evaluation(analysis.score, analysis.mate)]
		move = best_move or analysis.best_move
		if move:
			lines.append(describe_move(position.pieces if position else None, move))
		lines.append(f"Best move: {analysis.best_move_san} (depth {analysis.depth})")
		for line in analysis.lines[1:]:
			lines.append(f"Alternative: {line.san}  {format_line(line.score, line.mate)}")
		return "\n".join(lines)

	def _set_content(self, message: str) -> None:
		self.text.configure(state="normal")
		self.text.delete("1.0", "end")
		timestamp = time.strftime("%H:%M:%S")
		self.text.insert("end", f"[{timestamp}]\n{message}")
		self.text.configure(state="disabled")

	def close(self) -> None:
		self.stop_hotkey()
		if self.visible:
			self.hide()
		if self._owns_root:
			self.root.destroy()
		else:
			self.window.destroy()
