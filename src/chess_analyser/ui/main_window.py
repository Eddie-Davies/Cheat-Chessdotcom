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

from .status import format_evaluation, format_line


class MainWindow:
	"""Own the Tkinter widgets and coordinate asynchronous engine analysis."""

	def __init__(
		self,
		root: tk.Tk | None = None,
		*,
		engine: StockfishEngine | Any | None = None,
		settings: AppSettings | None = None,
	) -> None:
		self.settings = settings or DEFAULT_SETTINGS
		self.root = root or tk.Tk()
		self.engine = engine or StockfishEngine(self.settings.stockfish_path or None)
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
		self.engine_status_var = tk.StringVar(value="Stockfish: ready to start")
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
		ttk.Label(container, textvariable=self.engine_status_var).grid(
			row=1, column=0, columnspan=2, sticky="w", pady=(0, 12)
		)

		settings_frame = ttk.LabelFrame(container, text="Engine settings", padding=10)
		settings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		settings_frame.columnconfigure(1, weight=1)
		self._add_entry(settings_frame, 0, "Depth", self.depth_var)
		self._add_entry(settings_frame, 1, "Time (seconds)", self.time_var)
		self._add_entry(settings_frame, 2, "Lines (MultiPV)", self.multipv_var)

		fen_frame = ttk.LabelFrame(container, text="Diagnostic position (FEN)", padding=10)
		fen_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
		fen_frame.columnconfigure(0, weight=1)
		self.fen_entry = ttk.Entry(fen_frame, textvariable=self.fen_var)
		self.fen_entry.grid(row=0, column=0, sticky="ew")
		self.analyse_button = ttk.Button(fen_frame, text="Analyse", command=self._on_analyse)
		self.analyse_button.grid(row=0, column=1, padx=(8, 0))

		result_frame = ttk.LabelFrame(container, text="Analysis", padding=10)
		result_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
		result_frame.columnconfigure(1, weight=1)
		result_frame.rowconfigure(4, weight=1)
		container.rowconfigure(4, weight=1)
		self._add_result_value(result_frame, 0, "Best move", self.best_move_var)
		self._add_result_value(result_frame, 1, "Evaluation", self.evaluation_var)
		self._add_result_value(result_frame, 2, "Search depth", self.depth_display_var)
		ttk.Label(result_frame, text="Alternative moves").grid(row=3, column=0, sticky="nw", pady=(12, 4))
		self.alternatives = tk.Listbox(result_frame, height=6, exportselection=False)
		self.alternatives.grid(row=4, column=0, columnspan=2, sticky="nsew")

		ttk.Label(container, textvariable=self.status_var, relief="sunken", anchor="w").grid(
			row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0)
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
		self.engine.stop()
		self.root.destroy()
