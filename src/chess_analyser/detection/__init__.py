"""Detection public API with lazy imports for module execution."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .board_detector import BoardDetection, BoardDetector
	from .orientation import OrientationDetection, OrientationDetector
	from .piece_detector import OccupancyDetection, OccupancyDetector, PieceDetection, PieceDetector, TemplatePieceDetector
	from .square_detector import SquareDetector, SquareDetection

__all__ = [
	"BoardDetection",
	"BoardDetector",
	"OrientationDetection",
	"OrientationDetector",
	"OccupancyDetection",
	"OccupancyDetector",
	"PieceDetection",
	"PieceDetector",
	"TemplatePieceDetector",
	"SquareDetector",
	"SquareDetection",
]


def __getattr__(name: str):
	if name in __all__:
		from .board_detector import BoardDetection, BoardDetector
		from .orientation import OrientationDetection, OrientationDetector
		from .piece_detector import OccupancyDetection, OccupancyDetector, PieceDetection, PieceDetector, TemplatePieceDetector
		from .square_detector import SquareDetector, SquareDetection

		return {
			"BoardDetection": BoardDetection,
			"BoardDetector": BoardDetector,
			"OrientationDetection": OrientationDetection,
			"OrientationDetector": OrientationDetector,
			"OccupancyDetection": OccupancyDetection,
			"OccupancyDetector": OccupancyDetector,
			"PieceDetection": PieceDetection,
			"PieceDetector": PieceDetector,
			"TemplatePieceDetector": TemplatePieceDetector,
			"SquareDetector": SquareDetector,
			"SquareDetection": SquareDetection,
		}[name]
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
