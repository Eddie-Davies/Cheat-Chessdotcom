"""Detection public API with lazy imports for module execution."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .board_detector import BoardDetection, BoardDetector

__all__ = ["BoardDetection", "BoardDetector"]


def __getattr__(name: str):
	if name in __all__:
		from .board_detector import BoardDetection, BoardDetector

		return {"BoardDetection": BoardDetection, "BoardDetector": BoardDetector}[name]
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
