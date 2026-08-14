"""Minimal cross-platform Tkinter control window for Chess Analyser."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from chess_analyser.engine import StockfishEngine
from chess_analyser.config import AppSettings, DEFAULT_SETTINGS
from chess_analyser.overlay import GlobalHotkeyService
from chess_analyser.pipeline import AutomaticAnalysisPipeline, PipelineEvent

from .calibration import BoardCalibration, BoardCalibrationWindow


class MainWindow:
	"""Minimal control window: Start/Stop monitoring and detect/calibrate the board.

	Engine, capture, and detection settings all use their AppSettings defaults
	behind the scenes; there is intentionally no settings UI to configure them.
	"""

	_SITE_LABELS = {"chesscom": "Chess.com", "lichess": "Lichess"}
	_SITE_KEYS = {"Chess.com": "chesscom", "Lichess": "lichess"}

	def __init__(
		self,
		root: tk.Tk | None = None,
		*,
		engine: StockfishEngine | Any | None = None,
		pipeline: AutomaticAnalysisPipeline | Any | None = None,
		overlay: Any | None = None,
		settings: AppSettings | None = None,
	) -> None:
		self.settings = settings or DEFAULT_SETTINGS
		self.root = root or tk.Tk()
		self.engine = engine or StockfishEngine(self.settings.stockfish_path or None)
		self.pipeline = pipeline
		self.overlay = overlay
		self.calibration: BoardCalibration | None = None
		self._running = False
		self._closed = False
		self._window_visible = True

		self.root.title("Chess Analyser")
		self.root.minsize(280, 140)
		self.root.attributes("-topmost", True)
		self.root.protocol("WM_DELETE_WINDOW", self.close)
		self.status_var = tk.StringVar(value="Ready")
		self.site_var = tk.StringVar(value=self._SITE_LABELS.get(self.settings.site, "Chess.com"))
		self._build_widgets()
		self._position_bottom_right()
		self.window_hotkey_service = GlobalHotkeyService(key="f9")
		status = self.window_hotkey_service.start(self._toggle_window_visibility_threadsafe)
		if not status.registered:
			self.status_var.set(status.message)

	def _build_widgets(self) -> None:
		container = ttk.Frame(self.root, padding=16)
		container.grid(row=0, column=0, sticky="nsew")
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

		ttk.Label(container, text="CHESS ANALYSER", font=("TkDefaultFont", 16, "bold")).grid(
			row=0, column=0, sticky="w", pady=(0, 14)
		)

		controls_frame = ttk.Frame(container)
		controls_frame.grid(row=1, column=0, sticky="ew")
		self.start_button = ttk.Button(controls_frame, text="Start", command=self._toggle_monitoring)
		self.start_button.pack(side="left")
		self.calibrate_button = ttk.Button(controls_frame, text="Detect Board", command=self.calibrate_board)
		self.calibrate_button.pack(side="left", padx=(6, 0))
		self.site_combo = ttk.Combobox(
			controls_frame,
			textvariable=self.site_var,
			values=list(self._SITE_KEYS),
			state="readonly",
			width=10,
		)
		self.site_combo.pack(side="left", padx=(6, 0))

		ttk.Label(container, textvariable=self.status_var, relief="sunken", anchor="w").grid(
			row=2, column=0, sticky="ew", pady=(12, 0)
		)

	def _toggle_window_visibility_threadsafe(self) -> None:
		"""Called from the hotkey listener thread; marshal onto the Tk thread."""
		self.root.after(0, self._toggle_window_visibility)

	def _toggle_window_visibility(self) -> None:
		if self._window_visible:
			self.root.withdraw()
		else:
			self.root.deiconify()
			self.root.attributes("-topmost", True)
			self._position_bottom_right()
		self._window_visible = not self._window_visible

	def _position_bottom_right(self) -> None:
		self.root.update_idletasks()
		width = self.root.winfo_width()
		height = self.root.winfo_height()
		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()
		x = max(0, screen_width - width - 10)
		y = max(0, screen_height - height - 60)
		self.root.geometry(f"+{x}+{y}")

	def _create_pipeline(self) -> AutomaticAnalysisPipeline:
		from chess_analyser.capture import ScreenCapture
		from chess_analyser.detection import BoardDetector, ChessComClockDetector, LichessClockDetector, TemplatePieceDetector

		site = self._SITE_KEYS.get(self.site_var.get(), "chesscom")
		if site == "lichess":
			template_dir = "assets/piece_templates/lichess"
			clock_detector = LichessClockDetector()
		else:
			template_dir = "assets/piece_templates"
			clock_detector = ChessComClockDetector()

		return AutomaticAnalysisPipeline(
			capture=ScreenCapture(),
			board_detector=BoardDetector(min_confidence=self.settings.board_confidence_threshold),
			piece_detector=TemplatePieceDetector(template_dir),
			clock_detector=clock_detector,
			engine=self.engine,
			capture_interval_ms=self.settings.capture_interval_ms,
			board_detection_interval_ms=self.settings.board_detection_interval_ms,
			board_confidence_threshold=self.settings.board_confidence_threshold,
			piece_confidence_threshold=self.settings.piece_confidence_threshold,
			engine_depth=self.settings.engine_depth,
			engine_time_ms=self.settings.engine_time_ms,
			engine_multipv=self.settings.multipv,
			event_callback=self._on_pipeline_event,
		)

	def _toggle_monitoring(self) -> None:
		if self._running:
			self.pause()
		else:
			self.start()

	def start(self) -> None:
		"""Start automatic monitoring without blocking Tkinter."""
		if self._running:
			return
		if self.pipeline is None:
			self.pipeline = self._create_pipeline()
		else:
			self.pipeline.event_callback = self._on_pipeline_event
		if self.calibration is not None:
			self.pipeline.set_manual_calibration(
				x=self.calibration.x,
				y=self.calibration.y,
				width=self.calibration.width,
				height=self.calibration.height,
				orientation=self.calibration.orientation,
			)
		try:
			self.pipeline.start()
		except Exception as exc:
			self.status_var.set(f"Unable to start monitoring: {exc}")
			return
		self._running = True
		self._ensure_overlay()
		# Shown immediately (blank until a move is available); only F8 hides it.
		self.overlay.show()
		self.start_button.configure(text="Stop")
		self.site_combo.configure(state="disabled")
		self.status_var.set("Monitoring started")

	def pause(self) -> None:
		"""Stop monitoring and leave the control window responsive."""
		if self.pipeline:
			self.pipeline.stop()
			self.pipeline = None
		self._running = False
		self.start_button.configure(text="Start")
		self.site_combo.configure(state="readonly")
		self.status_var.set("Stopped")

	def _ensure_overlay(self) -> None:
		if self.overlay is not None:
			return
		from chess_analyser.overlay import MovePanel

		# A docked side panel, not an on-board overlay, so it never appears
		# inside the region being screen-captured for board/piece detection.
		self.overlay = MovePanel(self.root)
		status = self.overlay.start_hotkey()
		if not status.registered:
			self.status_var.set(status.message)

	def calibrate_board(self) -> None:
		"""Let the user click the board's corners and pick a color instead of
		relying on automatic detection; see AGENTS.md 3.5 for this fallback."""
		BoardCalibrationWindow(self.root, on_complete=self._apply_calibration)

	def _apply_calibration(self, calibration: BoardCalibration) -> None:
		self.calibration = calibration
		color = "White" if calibration.orientation == "white_bottom" else "Black"
		if self.pipeline is not None:
			self.pipeline.set_manual_calibration(
				x=calibration.x,
				y=calibration.y,
				width=calibration.width,
				height=calibration.height,
				orientation=calibration.orientation,
			)
		self.status_var.set(f"Board detected ({color}, {calibration.width}x{calibration.height})")

	def clear_calibration(self) -> None:
		"""Return to automatic board/orientation detection."""
		self.calibration = None
		if self.pipeline is not None:
			self.pipeline.clear_manual_calibration()
		self.status_var.set("Using automatic board detection")

	def _on_pipeline_event(self, event: PipelineEvent) -> None:
		"""Marshal pipeline callbacks from worker threads to the Tk thread."""
		if self._closed:
			return
		self.root.after(0, lambda: self._apply_pipeline_event(event))

	def _apply_pipeline_event(self, event: PipelineEvent) -> None:
		if event.state == "ANALYSIS_READY" and event.board is not None and event.analysis is not None:
			self._ensure_overlay()
			user_color = "white" if event.board.orientation == "white_bottom" else "black"
			if event.position is not None and event.position.side_to_move == user_color:
				self.overlay.update(event.board, event.analysis.best_move, event.analysis, position=event.position)
			else:
				# Not the user's color to move; never suggest the opponent's move.
				self.overlay.set_status("Waiting for opponent's move...")
		# The panel's visibility is only ever controlled by the user's F8
		# hotkey; no pipeline state here shows or hides it.
		self.status_var.set(event.message or event.state)

	def run(self) -> None:
		"""Start the Tkinter event loop."""
		self.root.mainloop()

	def close(self) -> None:
		"""Stop engine work and close the window."""
		if self._closed:
			return
		self._closed = True
		self.window_hotkey_service.stop()
		if self.pipeline:
			self.pipeline.stop()
		else:
			self.engine.stop()
		if self.overlay:
			self.overlay.close()
		self.root.destroy()

