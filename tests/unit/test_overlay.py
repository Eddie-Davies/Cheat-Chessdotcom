"""Phase 14 overlay contract and diagnostic backend tests."""

from chess_analyser.detection import BoardDetection
from chess_analyser.overlay import OverlayGeometry, OverlayPlatform


def test_overlay_geometry_comes_from_board_detection():
	board = BoardDetection(247.4, 152.2, 928.7, 927.6, 116.0, 0.86)

	geometry = OverlayGeometry.from_board(board)

	assert geometry == OverlayGeometry(247, 152, 929, 928)


def test_overlay_geometry_rejects_no_assumptions_about_resolution():
	board = BoardDetection(11, 23, 317, 289, 39.625, 0.8)

	geometry = OverlayGeometry.from_board(board)

	assert (geometry.x, geometry.y) == (11, 23)
	assert (geometry.width, geometry.height) == (317, 289)


def test_platform_capability_report_is_available():
	platform_info = OverlayPlatform()

	assert platform_info.system
	assert isinstance(platform_info.notes, tuple)


def test_overlay_interface_is_not_click_through_by_contract():
	from chess_analyser.overlay import Overlay

	assert "click" not in Overlay.__doc__.lower()


def test_tkinter_backend_is_importable_for_manual_diagnostics():
	from chess_analyser.overlay import TkinterOverlay

	assert callable(TkinterOverlay)