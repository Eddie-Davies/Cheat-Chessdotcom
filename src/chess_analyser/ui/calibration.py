"""Manual board calibration: click two corners and pick your starting color.

Automatic detection remains the primary path (see AGENTS.md 3.5); this is an
explicit opt-in fallback so the pipeline can skip full-screen detection
entirely once the board region and player color are verified by hand.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class BoardCalibration:
	"""User-verified board bounds and starting color."""

	x: int
	y: int
	width: int
	height: int
	orientation: str


class BoardCalibrationWindow:
	"""Fullscreen click-to-calibrate overlay; never sends input to other apps."""

	def __init__(
		self,
		root: tk.Misc,
		*,
		on_complete: Callable[[BoardCalibration], None],
		on_cancel: Callable[[], None] | None = None,
	) -> None:
		self.root = root
		self.on_complete = on_complete
		self.on_cancel = on_cancel
		self._first_point: tuple[int, int] | None = None
		self.window = tk.Toplevel(root)
		self.window.attributes("-topmost", True)
		self.window.attributes("-alpha", 0.35)
		self.window.configure(bg="#000000")
		self.window.overrideredirect(True)
		width = self.window.winfo_screenwidth()
		height = self.window.winfo_screenheight()
		self.window.geometry(f"{width}x{height}+0+0")
		self.canvas = tk.Canvas(self.window, bg="#000000", highlightthickness=0, cursor="crosshair")
		self.canvas.pack(fill="both", expand=True)
		self.label = self.canvas.create_text(
			width // 2,
			40,
			text="Click the board's TOP-LEFT corner (Esc to cancel)",
			fill="#ffffff",
			font=("TkDefaultFont", 16, "bold"),
		)
		self.canvas.bind("<Button-1>", self._on_click)
		self.window.bind("<Escape>", lambda _event: self.cancel())
		self.window.focus_force()

	def _on_click(self, event: tk.Event) -> None:
		if self._first_point is None:
			self._first_point = (event.x_root, event.y_root)
			self.canvas.create_oval(
				event.x - 5, event.y - 5, event.x + 5, event.y + 5, outline="#49d17d", width=3
			)
			self.canvas.itemconfigure(self.label, text="Click the board's BOTTOM-RIGHT corner")
			return
		x1, y1 = self._first_point
		x2, y2 = event.x_root, event.y_root
		x, y = min(x1, x2), min(y1, y2)
		width, height = abs(x2 - x1), abs(y2 - y1)
		self.window.destroy()
		if width < 50 or height < 50:
			if self.on_cancel:
				self.on_cancel()
			return
		self._ask_color(x, y, width, height)

	def _ask_color(self, x: int, y: int, width: int, height: int) -> None:
		dialog = tk.Toplevel(self.root)
		dialog.title("Starting color")
		dialog.attributes("-topmost", True)
		dialog.resizable(False, False)
		tk.Label(dialog, text="Which color are you playing?", padx=16, pady=12).pack()
		buttons = tk.Frame(dialog, padx=16, pady=12)
		buttons.pack()

		def choose(orientation: str) -> None:
			dialog.destroy()
			self.on_complete(BoardCalibration(x, y, width, height, orientation))

		tk.Button(buttons, text="White (bottom)", command=lambda: choose("white_bottom")).pack(side="left", padx=6)
		tk.Button(buttons, text="Black (bottom)", command=lambda: choose("black_bottom")).pack(side="left", padx=6)
		dialog.protocol("WM_DELETE_WINDOW", lambda: (dialog.destroy(), self.on_cancel() if self.on_cancel else None))

	def cancel(self) -> None:
		self.window.destroy()
		if self.on_cancel:
			self.on_cancel()
