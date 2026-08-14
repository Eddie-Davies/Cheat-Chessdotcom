"""Tests for the brief on-board move-arrow flash overlay."""

import tkinter as tk

import pytest

from chess_analyser.detection import BoardDetection
from chess_analyser.overlay import ArrowFlashOverlay


def create_overlay_or_skip(**kwargs):
	try:
		root = tk.Tk()
	except tk.TclError as exc:
		pytest.skip(f"Tkinter display unavailable: {exc}")
	root.withdraw()
	overlay = ArrowFlashOverlay(root, **kwargs)
	return root, overlay


def test_flash_shows_the_overlay_and_draws_one_arrow():
	root, overlay = create_overlay_or_skip(duration_ms=5000)
	try:
		board = BoardDetection(100, 50, 400, 400, 50.0, 0.9, "white_bottom")

		overlay.flash(board, "e2e4")

		assert overlay.visible is True
		assert len(overlay.canvas.find_withtag("move-arrow")) == 1
	finally:
		overlay.close()


def test_flash_auto_hides_after_duration():
	root, overlay = create_overlay_or_skip(duration_ms=20)
	try:
		board = BoardDetection(0, 0, 400, 400, 50.0, 0.9, "white_bottom")

		overlay.flash(board, "e2e4")
		assert overlay.visible is True

		root.update()
		root.after(60, root.quit)
		root.mainloop()

		assert overlay.visible is False
	finally:
		overlay.close()


def test_repeated_flash_replaces_the_previous_arrow_and_timer():
	root, overlay = create_overlay_or_skip(duration_ms=5000)
	try:
		board = BoardDetection(0, 0, 400, 400, 50.0, 0.9, "white_bottom")

		overlay.flash(board, "e2e4")
		overlay.flash(board, "d2d4")

		assert len(overlay.canvas.find_withtag("move-arrow")) == 1
	finally:
		overlay.close()


def test_hide_cancels_a_pending_auto_hide_job():
	root, overlay = create_overlay_or_skip(duration_ms=5000)
	try:
		board = BoardDetection(0, 0, 400, 400, 50.0, 0.9, "white_bottom")

		overlay.flash(board, "e2e4")
		overlay.hide()

		assert overlay.visible is False
		assert overlay._hide_job is None
	finally:
		overlay.close()


def test_hotkey_reflashes_the_last_pending_move():
	root, overlay = create_overlay_or_skip(duration_ms=5000)
	try:
		board = BoardDetection(0, 0, 400, 400, 50.0, 0.9, "white_bottom")
		overlay.set_pending_move(board, "e2e4")

		overlay._flash_pending()

		assert overlay.visible is True
	finally:
		overlay.close()


def test_duration_must_be_positive():
	with pytest.raises(ValueError):
		ArrowFlashOverlay(duration_ms=0)
