"""Platform-neutral overlay contract and Tkinter diagnostic backend."""

from __future__ import annotations

import argparse
import os
import platform
import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2

from chess_analyser.detection.board_detector import BoardDetection
from chess_analyser.detection.square_detector import SquareDetector


@dataclass(frozen=True)
class OverlayGeometry:
	"""Screen-space geometry used by an overlay backend."""

	x: int
	y: int
	width: int
	height: int

	@classmethod
	def from_board(cls, board: BoardDetection) -> "OverlayGeometry":
		return cls(round(board.x), round(board.y), round(board.width), round(board.height))


class Overlay(ABC):
	"""Cross-platform overlay interface."""

	@abstractmethod
	def show(self) -> None:
		"""Show the overlay."""

	@abstractmethod
	def hide(self) -> None:
		"""Hide the overlay."""

	@abstractmethod
	def update(self, board: BoardDetection) -> None:
		"""Move and redraw the overlay for detected board geometry."""

	@abstractmethod
	def close(self) -> None:
		"""Release overlay resources."""


class OverlayPlatform:
	"""Capabilities and known limitations of the current desktop session."""

	def __init__(self) -> None:
		self.system = platform.system()
		self.display_session = "unknown"
		if self.system == "Linux":
			self.display_session = os.environ.get("XDG_SESSION_TYPE", "unknown")

	@property
	def notes(self) -> tuple[str, ...]:
		notes = []
		if self.system == "Darwin":
			notes.append("macOS may require Screen Recording/accessibility permissions for screen-aligned workflows.")
		if self.system == "Linux":
			notes.append("Wayland compositors may restrict global positioning and always-on-top behavior; X11 is better supported by Tkinter.")
		return tuple(notes)


class TkinterOverlay(Overlay):
	"""Borderless, translucent, always-on-top grid overlay using Tk APIs."""

	def __init__(self, root: tk.Misc | None = None, *, alpha: float = 0.82) -> None:
		if not 0 < alpha <= 1:
			raise ValueError("alpha must be greater than 0 and at most 1")
		self._owns_root = root is None
		self.root = root or tk.Tk()
		self.window = self.root if root is None else tk.Toplevel(root)
		self.alpha = alpha
		self.visible = False
		self.geometry: OverlayGeometry | None = None
		self.window.overrideredirect(True)
		self.window.attributes("-topmost", True)
		self.window.attributes("-alpha", alpha)
		self.canvas = tk.Canvas(self.window, highlightthickness=0, bd=0, bg="#101820")
		self.canvas.pack(fill="both", expand=True)
		self.window.protocol("WM_DELETE_WINDOW", self.close)

	def show(self) -> None:
		self.window.deiconify()
		self.window.attributes("-topmost", True)
		self.visible = True

	def hide(self) -> None:
		self.window.withdraw()
		self.visible = False

	def update(self, board: BoardDetection) -> None:
		self.geometry = OverlayGeometry.from_board(board)
		geometry = self.geometry
		self.window.geometry(f"{geometry.width}x{geometry.height}+{geometry.x}+{geometry.y}")
		self._draw_grid()
		if not self.visible:
			self.show()

	def _draw_grid(self) -> None:
		if self.geometry is None:
			return
		self.canvas.delete("all")
		width, height = self.geometry.width, self.geometry.height
		for index in range(9):
			x = round(width * index / 8)
			y = round(height * index / 8)
			self.canvas.create_line(x, 0, x, height, fill="#49d17d", width=2)
			self.canvas.create_line(0, y, width, y, fill="#49d17d", width=2)

	def run_diagnostic(self, board: BoardDetection) -> None:
		"""Position the test grid over a supplied board and enter Tk's loop."""
		self.update(board)
		self.root.mainloop()

	def close(self) -> None:
		if self.visible:
			self.hide()
		if self._owns_root:
			self.root.destroy()
		else:
			self.window.destroy()


def main() -> None:
	"""Run a manual diagnostic overlay using explicit test geometry."""
	parser = argparse.ArgumentParser(description="Show a diagnostic Chess Analyser overlay")
	parser.add_argument("--x", type=int, required=True)
	parser.add_argument("--y", type=int, required=True)
	parser.add_argument("--width", type=int, required=True)
	parser.add_argument("--height", type=int, required=True)
	args = parser.parse_args()
	board = BoardDetection(args.x, args.y, args.width, args.height, args.width / 8, 1.0)
	TkinterOverlay().run_diagnostic(board)


if __name__ == "__main__":
	main()
