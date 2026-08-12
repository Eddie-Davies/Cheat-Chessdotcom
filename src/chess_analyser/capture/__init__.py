"""Screen capture public API with lazy imports for module execution."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .screen_capture import MonitorInfo, ScreenCapture, ScreenCaptureError

__all__ = ["MonitorInfo", "ScreenCapture", "ScreenCaptureError"]


def __getattr__(name: str):
	if name in __all__:
		from .screen_capture import MonitorInfo, ScreenCapture, ScreenCaptureError

		return {
			"MonitorInfo": MonitorInfo,
			"ScreenCapture": ScreenCapture,
			"ScreenCaptureError": ScreenCaptureError,
		}[name]
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
