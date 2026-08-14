"""Brief on-board arrow flash: shows the suggested move directly over the
board for a moment, then auto-hides so it never lingers into later screen
captures used for board/piece detection.

Unlike MovePanel (a permanent side-docked panel), this window is aligned to
the board itself and is only ever visible for a short, bounded duration.
"""

from __future__ import annotations

import platform
import tkinter as tk
from typing import Any

from .arrows import ArrowRenderer
from .hotkeys import GlobalHotkeyService, HotkeyStatus

# An arbitrary color unlikely to appear in a real chessboard/piece render;
# on Windows this becomes fully transparent so only the arrow line is visible.
_CHROMA_KEY = "#123456"


class ArrowFlashOverlay:
	"""Borderless, always-on-top window that flashes a move arrow over the board."""

	def __init__(
		self,
		root: tk.Misc | None = None,
		*,
		duration_ms: int = 1200,
		color: str = "#ffcc33",
		width: int = 8,
		hotkey_service: GlobalHotkeyService | None = None,
	) -> None:
		if duration_ms <= 0:
			raise ValueError("duration_ms must be greater than 0")
		self._owns_root = root is None
		self.root = root or tk.Tk()
		self.window = self.root if root is None else tk.Toplevel(root)
		self.duration_ms = duration_ms
		self.color = color
		self.line_width = width
		self.visible = False
		self.arrow_renderer = ArrowRenderer()
		self.hotkey_service = hotkey_service
		self._hide_job: str | None = None
		self._board: Any | None = None
		self._pending_move: str | None = None

		self.window.overrideredirect(True)
		self.window.attributes("-topmost", True)
		# Chroma-key transparency is a Windows-only Tk feature; other platforms
		# fall back to a translucent tint (a documented, lesser experience).
		self._chroma_key_supported = platform.system() == "Windows"
		if self._chroma_key_supported:
			self.window.attributes("-transparentcolor", _CHROMA_KEY)
			background = _CHROMA_KEY
		else:
			self.window.attributes("-alpha", 0.85)
			background = "#101820"
		self.canvas = tk.Canvas(self.window, highlightthickness=0, bd=0, bg=background)
		self.canvas.pack(fill="both", expand=True)
		self.window.protocol("WM_DELETE_WINDOW", self.close)
		self.window.withdraw()

	def flash(self, board: Any, uci_move: str) -> None:
		"""Show the move arrow over the board, then auto-hide after duration_ms."""
		self.set_pending_move(board, uci_move)
		self._cancel_pending_hide()
		self.window.geometry(f"{round(board.width)}x{round(board.height)}+{round(board.x)}+{round(board.y)}")
		self.canvas.delete("all")
		self.arrow_renderer.draw_on_canvas(self.canvas, board, uci_move, color=self.color, width=self.line_width)
		self.show()
		self._hide_job = self.window.after(self.duration_ms, self.hide)

	def show(self) -> None:
		self.window.deiconify()
		self.window.attributes("-topmost", True)
		self.visible = True

	def hide(self) -> None:
		self._cancel_pending_hide()
		self.window.withdraw()
		self.visible = False

	def set_pending_move(self, board: Any, uci_move: str | None) -> None:
		"""Cache the latest board/move so the hotkey can re-flash it on demand."""
		self._board = board
		self._pending_move = uci_move

	def start_hotkey(self, service: GlobalHotkeyService | None = None, *, key: str = "f10") -> HotkeyStatus:
		"""Register a global hotkey that re-flashes the last known move."""
		self.hotkey_service = service or self.hotkey_service or GlobalHotkeyService(key=key)
		return self.hotkey_service.start(self._trigger_from_hotkey)

	def stop_hotkey(self) -> None:
		if self.hotkey_service:
			self.hotkey_service.stop()

	def _trigger_from_hotkey(self) -> None:
		"""Called from the hotkey listener thread; marshal onto the Tk thread."""
		self.root.after(0, self._flash_pending)

	def _flash_pending(self) -> None:
		if self._board is not None and self._pending_move:
			self.flash(self._board, self._pending_move)

	def _cancel_pending_hide(self) -> None:
		if self._hide_job is not None:
			self.window.after_cancel(self._hide_job)
			self._hide_job = None

	def close(self) -> None:
		self.stop_hotkey()
		self._cancel_pending_hide()
		if self.visible:
			self.hide()
		if self._owns_root:
			self.root.destroy()
		else:
			self.window.destroy()
