"""Unit tests for the Phase 4 screen capture API."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from chess_analyser.capture import ScreenCapture, ScreenCaptureError


class FakeMSS:
    def __init__(self):
        self.monitors = [
            {"left": 0, "top": 0, "width": 300, "height": 200},
            {"left": 10, "top": 20, "width": 100, "height": 80},
            {"left": 110, "top": 20, "width": 120, "height": 90},
        ]
        self.grab_calls = []
        self.closed = False

    def grab(self, region):
        self.grab_calls.append(region)
        return np.array(
            [
                [[10, 20, 30, 255], [40, 50, 60, 255]],
                [[70, 80, 90, 255], [100, 110, 120, 255]],
            ],
            dtype=np.uint8,
        )

    def close(self):
        self.closed = True


def test_monitor_enumeration_excludes_virtual_combined_monitor():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        monitors = capture.monitors()

        assert [(monitor.index, monitor.x, monitor.width) for monitor in monitors] == [
            (1, 10, 100),
            (2, 110, 120),
        ]
        assert monitors[0].region == {"left": 10, "top": 20, "width": 100, "height": 80}
    finally:
        capture.close()


def test_primary_capture_returns_bgr_opencv_array():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        image = capture.capture()

        assert image.shape == (2, 2, 3)
        assert image.dtype == np.uint8
        assert image[0, 0].tolist() == [10, 20, 30]
        assert backend.grab_calls == [
            {"left": 10, "top": 20, "width": 100, "height": 80}
        ]
    finally:
        capture.close()


def test_region_capture_accepts_tuple_and_monitor_capture():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        capture.capture_region((5, 6, 20, 30))
        capture.capture_monitor(2)

        assert backend.grab_calls == [
            {"left": 5, "top": 6, "width": 20, "height": 30},
            {"left": 110, "top": 20, "width": 120, "height": 90},
        ]
    finally:
        capture.close()


def test_async_capture_returns_future():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        future = capture.capture_async((1, 2, 3, 4))
        image = future.result(timeout=2)

        assert isinstance(image, np.ndarray)
        assert backend.grab_calls == [{"left": 1, "top": 2, "width": 3, "height": 4}]
    finally:
        capture.close()


def test_diagnostic_screenshot_is_saved(tmp_path: Path):
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        output = capture.save_diagnostic_screenshot(tmp_path / "screens" / "capture.png")

        assert output == (tmp_path / "screens" / "capture.png").resolve()
        saved = cv2.imread(str(output))
        assert saved is not None
        assert saved.shape == (2, 2, 3)
    finally:
        capture.close()


def test_invalid_regions_and_monitors_are_rejected():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    try:
        with pytest.raises(ValueError, match="greater than zero"):
            capture.capture_region((0, 0, 0, 10))
        with pytest.raises(ScreenCaptureError, match="Monitor 3"):
            capture.capture_monitor(3)
    finally:
        capture.close()


def test_close_releases_backend_and_rejects_new_async_work():
    backend = FakeMSS()
    capture = ScreenCapture(backend=backend)
    capture.close()
    capture.close()

    assert backend.closed
    with pytest.raises(ScreenCaptureError, match="closed"):
        capture.capture_async()