"""Detection public API with lazy imports for module execution."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .board_detector import BoardDetection, BoardDetector
	from .square_detector import SquareDetector, SquareDetection

__all__ = ["BoardDetection", "BoardDetector", "SquareDetector", "SquareDetection"]


def __getattr__(name: str):
	if name in __all__:
		from .board_detector import BoardDetection, BoardDetector
		from .square_detector import SquareDetector, SquareDetection

		return {
			"BoardDetection": BoardDetection,
			"BoardDetector": BoardDetector,
			"SquareDetector": SquareDetector,
			"SquareDetection": SquareDetection,
		}[name]
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
