"""Overlay public API."""

from .arrows import ArrowGeometry, ArrowRenderer
# hotkeys must load before evaluation_panel: evaluation_panel pulls in
# chess_analyser.ui, whose main_window imports GlobalHotkeyService back from here.
from .hotkeys import (
	GlobalHotkeyService,
	HotkeyBackend,
	HotkeyError,
	HotkeyPermissionError,
	HotkeyStatus,
	HotkeyUnavailableError,
	OverlayVisibilityController,
)
from .evaluation_panel import EvaluationPanel, EvaluationPanelConfig
from .move_panel import MovePanel, describe_move
from .overlay_window import Overlay, OverlayGeometry, OverlayPlatform, TkinterOverlay

__all__ = [
	"ArrowGeometry",
	"ArrowRenderer",
	"EvaluationPanel",
	"EvaluationPanelConfig",
	"GlobalHotkeyService",
	"HotkeyBackend",
	"HotkeyError",
	"HotkeyPermissionError",
	"HotkeyStatus",
	"HotkeyUnavailableError",
	"MovePanel",
	"describe_move",
	"Overlay",
	"OverlayGeometry",
	"OverlayPlatform",
	"OverlayVisibilityController",
	"TkinterOverlay",
]
