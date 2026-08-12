"""Cross-platform screen capture using MSS and OpenCV-compatible arrays."""

from __future__ import annotations

import logging
import argparse
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import cv2
import mss
import numpy as np


class ScreenCaptureError(RuntimeError):
	"""Raised when a screen capture operation cannot be completed."""


@dataclass(frozen=True)
class MonitorInfo:
	"""Screen-space geometry for one monitor."""

	index: int
	x: int
	y: int
	width: int
	height: int

	@property
	def region(self) -> dict[str, int]:
		"""Return geometry in the format accepted by MSS."""
		return {"left": self.x, "top": self.y, "width": self.width, "height": self.height}


CaptureBackend = Callable[[], Any]


class ScreenCapture:
	"""Capture monitors or regions without assuming a display resolution."""

	def __init__(
		self,
		*,
		backend: Any | None = None,
		max_workers: int = 1,
		logger: logging.Logger | None = None,
	) -> None:
		self._backend = backend or mss.MSS()
		self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="screen-capture")
		self._logger = logger or logging.getLogger(__name__)
		self._closed = False

	def monitors(self) -> list[MonitorInfo]:
		"""Enumerate physical monitors, excluding MSS's virtual-all-monitors entry."""
		raw_monitors = getattr(self._backend, "monitors", None)
		if not raw_monitors or len(raw_monitors) < 2:
			return []
		return [self._monitor_from_raw(index, raw) for index, raw in enumerate(raw_monitors[1:], 1)]

	def primary_monitor(self) -> MonitorInfo:
		"""Return the primary monitor reported by MSS."""
		raw_monitors = getattr(self._backend, "monitors", None)
		if not raw_monitors:
			raise ScreenCaptureError("No monitors are available")
		return self._monitor_from_raw(1, raw_monitors[1] if len(raw_monitors) > 1 else raw_monitors[0])

	def capture(self) -> np.ndarray:
		"""Capture the primary monitor as a BGR ``numpy.ndarray``."""
		return self.capture_region(self.primary_monitor().region)

	def capture_monitor(self, monitor_index: int) -> np.ndarray:
		"""Capture a physical monitor by its one-based MSS index."""
		available = {monitor.index: monitor for monitor in self.monitors()}
		try:
			monitor = available[monitor_index]
		except KeyError as exc:
			raise ScreenCaptureError(f"Monitor {monitor_index} is not available") from exc
		return self.capture_region(monitor.region)

	def capture_region(
		self,
		region: Mapping[str, int] | tuple[int, int, int, int],
	) -> np.ndarray:
		"""Capture ``left, top, width, height`` as a BGR OpenCV image."""
		bounds = self._normalise_region(region)
		try:
			raw_image = np.asarray(self._backend.grab(bounds))
		except Exception as exc:
			raise ScreenCaptureError(f"Unable to capture screen region: {exc}") from exc
		if raw_image.ndim != 3 or raw_image.shape[2] not in (3, 4):
			raise ScreenCaptureError(f"Unexpected capture format: {raw_image.shape}")
		return raw_image[:, :, :3].copy()

	def capture_async(
		self,
		region: Mapping[str, int] | tuple[int, int, int, int] | None = None,
	) -> Future[np.ndarray]:
		"""Capture in a worker thread and return a future for UI-safe polling."""
		if self._closed:
			raise ScreenCaptureError("Screen capture is closed")
		task = self.capture if region is None else lambda: self.capture_region(region)
		return self._executor.submit(task)

	def save_screenshot(self, image: np.ndarray, path: str | Path) -> Path:
		"""Save an OpenCV-compatible image and return its resolved path."""
		output_path = Path(path).expanduser()
		output_path.parent.mkdir(parents=True, exist_ok=True)
		if not isinstance(image, np.ndarray) or image.ndim != 3:
			raise ScreenCaptureError("Screenshot must be a color numpy.ndarray")
		if not cv2.imwrite(str(output_path), image):
			raise ScreenCaptureError(f"Unable to save screenshot: {output_path}")
		self._logger.info("Saved diagnostic screenshot to %s", output_path)
		return output_path.resolve()

	def save_diagnostic_screenshot(self, path: str | Path | None = None) -> Path:
		"""Capture the primary monitor and save it under ``assets/test_screens`` by default."""
		output_path = Path(path) if path else Path("assets/test_screens/capture.png")
		return self.save_screenshot(self.capture(), output_path)

	def close(self) -> None:
		"""Release the capture backend and worker resources."""
		if self._closed:
			return
		self._closed = True
		self._executor.shutdown(wait=True)
		close = getattr(self._backend, "close", None)
		if close:
			close()

	def __enter__(self) -> "ScreenCapture":
		return self

	def __exit__(self, _exc_type: Any, _exc_value: Any, _traceback: Any) -> None:
		self.close()

	@staticmethod
	def _monitor_from_raw(index: int, raw: Mapping[str, int]) -> MonitorInfo:
		try:
			return MonitorInfo(index, raw["left"], raw["top"], raw["width"], raw["height"])
		except (KeyError, TypeError) as exc:
			raise ScreenCaptureError(f"Invalid monitor metadata: {raw}") from exc

	@staticmethod
	def _normalise_region(
		region: Mapping[str, int] | tuple[int, int, int, int],
	) -> dict[str, int]:
		if isinstance(region, tuple):
			if len(region) != 4:
				raise ValueError("Region tuple must contain left, top, width, height")
			left, top, width, height = region
		else:
			try:
				left, top = region["left"], region["top"]
				width, height = region["width"], region["height"]
			except (KeyError, TypeError) as exc:
				raise ValueError("Region must contain left, top, width, and height") from exc
		if not all(isinstance(value, int) for value in (left, top, width, height)):
			raise ValueError("Region coordinates and dimensions must be integers")
		if width <= 0 or height <= 0:
			raise ValueError("Region width and height must be greater than zero")
		return {"left": left, "top": top, "width": width, "height": height}


def main() -> None:
	"""Save a primary-monitor diagnostic image from the command line."""
	parser = argparse.ArgumentParser(description="Save a Chess Analyser screen capture")
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("assets/test_screens/capture.png"),
		help="PNG output path (default: assets/test_screens/capture.png)",
	)
	args = parser.parse_args()
	with ScreenCapture() as capture:
		output = capture.save_diagnostic_screenshot(args.output)
	print(f"Saved screenshot to {output}")


if __name__ == "__main__":
	main()
