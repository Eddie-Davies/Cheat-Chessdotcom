"""Basic cross-platform Tkinter interface for diagnostic position analysis."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any

from chess_analyser.chess import ChessPosition, PositionValidationError
from chess_analyser.engine import (
	EngineAnalysis,
	EngineError,
	StockfishEngine,
	StockfishUnavailableError,
)
from chess_analyser.config import AppSettings, DEFAULT_SETTINGS
from chess_analyser.pipeline import AutomaticAnalysisPipeline, PipelineEvent

from .status import format_evaluation, format_line


class MainWindow:
	"""Own the Tkinter widgets and coordinate asynchronous engine analysis."""

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
		self._running = False
		self._results: queue.Queue[tuple[str, object]] = queue.Queue()
		self._worker: threading.Thread | None = None
		self._closed = False

		self.root.title("Chess Analyser")
		self.root.minsize(560, 560)
		self.root.protocol("WM_DELETE_WINDOW", self.close)
		self._create_variables()
		self._build_widgets()
		self.root.after(50, self._poll_results)

	def _create_variables(self) -> None:
		self.depth_var = tk.StringVar(value=str(self.settings.engine_depth))
		self.time_var = tk.StringVar(value=f"{self.settings.engine_time_ms / 1000:.1f}")
		self.multipv_var = tk.StringVar(value=str(self.settings.multipv))
		self.fen_var = tk.StringVar(value=ChessPosition.starting().fen)
		self.board_status_var = tk.StringVar(value="Searching")
		self.board_confidence_var = tk.StringVar(value="-")
		self.position_status_var = tk.StringVar(value="Uncertain")
		self.pieces_status_var = tk.StringVar(value="0/32 recognised")
		self.engine_status_var = tk.StringVar(value="Stockfish")
		self.overlay_status_var = tk.StringVar(value="Hidden")
		self.hotkey_status_var = tk.StringVar(value=self.settings.overlay_hotkey.upper())
		self.best_move_var = tk.StringVar(value="-")
		self.evaluation_var = tk.StringVar(value="-")
		self.depth_display_var = tk.StringVar(value="-")
		self.status_var = tk.StringVar(value="Ready")

	def _build_widgets(self) -> None:
		container = ttk.Frame(self.root, padding=16)
		container.grid(row=0, column=0, sticky="nsew")
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)
		container.columnconfigure(1, weight=1)

		ttk.Label(container, text="CHESS ANALYSER", font=("TkDefaultFont", 18, "bold")).grid(
			row=0, column=0, columnspan=2, sticky="w", pady=(0, 14)
		)
		monitor_frame = ttk.LabelFrame(container, text="Monitoring", padding=10)
		monitor_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		monitor_frame.columnconfigure(1, weight=1)
		for row, label, variable in (
			(0, "Board", self.board_status_var),
			(1, "Confidence", self.board_confidence_var),
			(2, "Position", self.position_status_var),
			(3, "Pieces", self.pieces_status_var),
			(4, "Engine", self.engine_status_var),
			(5, "Overlay", self.overlay_status_var),
			(6, "Hotkey", self.hotkey_status_var),
		):
			ttk.Label(monitor_frame, text=f"{label}:").grid(row=row, column=0, sticky="w", pady=2)
			ttk.Label(monitor_frame, textvariable=variable).grid(row=row, column=1, sticky="w", pady=2)

		settings_frame = ttk.LabelFrame(container, text="Engine settings", padding=10)
		settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		settings_frame.columnconfigure(1, weight=1)
		self._add_entry(settings_frame, 0, "Depth", self.depth_var)
		self._add_entry(settings_frame, 1, "Time (seconds)", self.time_var)
		self._add_entry(settings_frame, 2, "Lines (MultiPV)", self.multipv_var)

		controls_frame = ttk.Frame(container)
		controls_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		self.start_button = ttk.Button(controls_frame, text="Start", command=self.start)
		self.start_button.pack(side="left")
		self.pause_button = ttk.Button(controls_frame, text="Pause", command=self.pause, state="disabled")
		self.pause_button.pack(side="left", padx=(6, 0))
		self.show_overlay_button = ttk.Button(controls_frame, text="Show Overlay", command=self.show_overlay)
		self.show_overlay_button.pack(side="left", padx=(6, 0))
		self.hide_overlay_button = ttk.Button(controls_frame, text="Hide Overlay", command=self.hide_overlay)
		self.hide_overlay_button.pack(side="left", padx=(6, 0))
		self.redetect_button = ttk.Button(controls_frame, text="Re-detect Board", command=self.redetect)
		self.redetect_button.pack(side="left", padx=(6, 0))
		self.settings_button = ttk.Button(controls_frame, text="Settings", command=self.open_settings)
		self.settings_button.pack(side="right")

		fen_frame = ttk.LabelFrame(container, text="Diagnostic position (optional)", padding=10)
		fen_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		fen_frame.columnconfigure(0, weight=1)
		self.fen_entry = ttk.Entry(fen_frame, textvariable=self.fen_var)
		self.fen_entry.grid(row=0, column=0, sticky="ew")
		self.analyse_button = ttk.Button(fen_frame, text="Analyse", command=self._on_analyse)
		self.analyse_button.grid(row=0, column=1, padx=(8, 0))

		result_frame = ttk.LabelFrame(container, text="Latest analysis", padding=10)
		result_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")
		result_frame.columnconfigure(1, weight=1)
		result_frame.rowconfigure(4, weight=1)
		container.rowconfigure(5, weight=1)
		self._add_result_value(result_frame, 0, "Best move", self.best_move_var)
		self._add_result_value(result_frame, 1, "Evaluation", self.evaluation_var)
		self._add_result_value(result_frame, 2, "Search depth", self.depth_display_var)
		ttk.Label(result_frame, text="Alternative moves").grid(row=3, column=0, sticky="nw", pady=(12, 4))
		self.alternatives = tk.Listbox(result_frame, height=6, exportselection=False)
		self.alternatives.grid(row=4, column=0, columnspan=2, sticky="nsew")

		ttk.Label(container, textvariable=self.status_var, relief="sunken", anchor="w").grid(
			row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0)
		)

	@staticmethod
	def _add_entry(parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar) -> None:
		ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
		ttk.Entry(parent, textvariable=variable, width=12).grid(row=row, column=1, sticky="e", pady=3)

	@staticmethod
	def _add_result_value(parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar) -> None:
		ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="w", pady=3)
		ttk.Label(parent, textvariable=variable, font=("TkDefaultFont", 11, "bold")).grid(
			row=row, column=1, sticky="w", pady=3
		)

	def _create_pipeline(self) -> AutomaticAnalysisPipeline:
		from chess_analyser.capture import ScreenCapture

		return AutomaticAnalysisPipeline(
			capture=ScreenCapture(),
			capture_interval_ms=self.settings.capture_interval_ms,
			board_confidence_threshold=self.settings.board_confidence_threshold,
			piece_confidence_threshold=self.settings.piece_confidence_threshold,
			event_callback=self._on_pipeline_event,
		)

	def start(self) -> None:
		"""Start automatic monitoring without blocking Tkinter."""
		if self._running:
			return
		if self.pipeline is None:
			self.pipeline = self._create_pipeline()
		else:
			self.pipeline.event_callback = self._on_pipeline_event
		try:
			self.pipeline.start()
		except Exception as exc:
			self._set_error(f"Unable to start monitoring: {exc}")
			return
		self._running = True
		self.start_button.configure(state="disabled")
		self.pause_button.configure(state="normal")
		self.status_var.set("Monitoring started")

	def pause(self) -> None:
		"""Pause monitoring and leave the control window responsive."""
		if self.pipeline:
			self.pipeline.stop()
		self._running = False
		self.start_button.configure(state="normal")
		self.pause_button.configure(state="disabled")
		self.status_var.set("Paused")

	def show_overlay(self) -> None:
		if self.overlay is None:
			from chess_analyser.overlay import TkinterOverlay

			self.overlay = TkinterOverlay(self.root)
			self.overlay.start_hotkey()
		self.overlay.show()
		self.overlay_status_var.set("Visible")

	def hide_overlay(self) -> None:
		if self.overlay:
			self.overlay.hide()
		self.overlay_status_var.set("Hidden")

	def redetect(self) -> None:
		if self.pipeline and hasattr(self.pipeline, "position_tracker"):
			self.pipeline.position_tracker.reset()
		self.board_status_var.set("Searching")
		self.board_confidence_var.set("-")
		self.position_status_var.set("Uncertain")
		self.pieces_status_var.set("0/32 recognised")
		self.status_var.set("Board re-detection requested")

	def open_settings(self) -> None:
		window = tk.Toplevel(self.root)
		window.title("Chess Analyser Settings")
		window.transient(self.root)
		for row, label, value in (
			(0, "Capture interval (ms)", self.settings.capture_interval_ms),
			(1, "Stable frames", self.settings.position_stability_frames),
			(2, "Debounce (ms)", self.settings.position_debounce_ms),
			(3, "Hotkey", self.settings.overlay_hotkey.upper()),
		):
			ttk.Label(window, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=6)
			ttk.Label(window, text=str(value)).grid(row=row, column=1, sticky="w", padx=10, pady=6)
		ttk.Button(window, text="Close", command=window.destroy).grid(row=4, column=0, columnspan=2, pady=10)

	def _on_pipeline_event(self, event: PipelineEvent) -> None:
		"""Marshal pipeline callbacks from worker threads to the Tk thread."""
		if self._closed:
			return
		self.root.after(0, lambda: self._apply_pipeline_event(event))

	def _apply_pipeline_event(self, event: PipelineEvent) -> None:
		if event.state == "SEARCHING":
			self.hide_overlay()
		elif event.board is not None and self.overlay is not None:
			best_move = event.analysis.best_move if event.analysis else None
			self.overlay.update(event.board, best_move, event.analysis)
		if event.state in {"SEARCHING", "POSITION_UNCERTAIN", "ERROR"}:
			self.board_status_var.set("Searching" if event.state == "SEARCHING" else "Detected")
			self.position_status_var.set("Uncertain" if event.state != "ERROR" else "Error")
			self.status_var.set(event.message or event.state)
		elif event.board is not None:
			self.board_status_var.set("Detected")
			self.board_confidence_var.set(f"{event.board.confidence:.0%}")
		if event.position is not None:
			self.position_status_var.set("Stable" if event.stability and event.stability.stable else "Transition")
			self.pieces_status_var.set(f"{len(event.position.pieces)}/32 recognised")
		if event.analysis is not None:
			self._show_analysis(event.analysis)


	def _on_analyse(self) -> None:
		if self._worker and self._worker.is_alive():
			return
		try:
			depth = int(self.depth_var.get())
			time_ms = round(float(self.time_var.get()) * 1000)
			multipv = int(self.multipv_var.get())
			if depth < 1 or time_ms <= 0 or multipv < 1:
				raise ValueError
			position = ChessPosition.from_fen(self.fen_var.get().strip())
			position.validate()
		except (ValueError, PositionValidationError) as exc:
			self._set_error(f"Invalid analysis input: {exc}")
			return

		self.analyse_button.configure(state="disabled")
		self.status_var.set("Analysing...")
		self.engine_status_var.set("Stockfish: starting")
		self._worker = threading.Thread(
			target=self._analyse_worker,
			args=(position.fen, depth, time_ms, multipv),
			daemon=True,
		)
		self._worker.start()

	def _analyse_worker(self, fen: str, depth: int, time_ms: int, multipv: int) -> None:
		try:
			result = self.engine.analyse(fen, depth=depth, time_ms=time_ms, multipv=multipv)
			self._results.put(("success", result))
		except (EngineError, StockfishUnavailableError, ValueError) as exc:
			self._results.put(("error", str(exc)))
		except Exception as exc:  # Keep unexpected worker failures out of Tk callbacks.
			self._results.put(("error", f"Unexpected engine error: {exc}"))

	def _poll_results(self) -> None:
		if self._closed:
			return
		try:
			result_type, payload = self._results.get_nowait()
		except queue.Empty:
			self.root.after(50, self._poll_results)
			return

		self.analyse_button.configure(state="normal")
		if result_type == "success":
			self._show_analysis(payload)  # type: ignore[arg-type]
		else:
			self._set_error(str(payload))
		self.root.after(50, self._poll_results)

	def _show_analysis(self, analysis: EngineAnalysis) -> None:
		self.engine_status_var.set("Stockfish: running")
		self.best_move_var.set(analysis.best_move_san)
		self.evaluation_var.set(format_evaluation(analysis.score, analysis.mate))
		self.depth_display_var.set(str(analysis.depth))
		self.alternatives.delete(0, tk.END)
		for line in analysis.lines[1:]:
			self.alternatives.insert(
				tk.END,
				f"{line.san}  {format_line(line.score, line.mate)}  (depth {line.depth})",
			)
		self.status_var.set("Analysis complete")

	def _set_error(self, message: str) -> None:
		self.engine_status_var.set("Stockfish: unavailable" if "Stockfish" in message else "Stockfish: ready")
		self.status_var.set(message)

	def run(self) -> None:
		"""Start the Tkinter event loop."""
		self.root.mainloop()

	def close(self) -> None:
		"""Stop engine work and close the window."""
		if self._closed:
			return
		self._closed = True
		if self.pipeline:
			self.pipeline.stop()
		else:
			self.engine.stop()
		if self.overlay:
			self.overlay.close()
		self.root.destroy()
