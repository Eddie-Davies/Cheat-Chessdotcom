"""
Configuration and settings for Chess Analyser.
"""

from dataclasses import dataclass, field


@dataclass
class AppSettings:
    """Application configuration settings."""

    # Engine settings
    engine_depth: int = 20
    engine_time_ms: int = 5000
    multipv: int = 5

    # Detection settings
    capture_interval_ms: int = 100
    board_detection_interval_ms: int = 500
    position_stability_frames: int = 3
    position_debounce_ms: int = 0
    piece_confidence_threshold: float = 0.7
    board_confidence_threshold: float = 0.7

    # Overlay settings
    overlay_hotkey: str = "f8"
    overlay_alpha: float = 0.8
    show_evaluation: bool = True
    show_alternatives: bool = True

    # Debug settings
    debug_mode: bool = False
    log_level: str = "INFO"

    # Engine paths
    stockfish_path: str = ""

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.position_stability_frames < 1:
            raise ValueError("position_stability_frames must be at least 1")
        if self.position_debounce_ms < 0:
            raise ValueError("position_debounce_ms must not be negative")
        if not 0 <= self.piece_confidence_threshold <= 1.0:
            raise ValueError("piece_confidence_threshold must be between 0 and 1")
        if not 0 <= self.board_confidence_threshold <= 1.0:
            raise ValueError("board_confidence_threshold must be between 0 and 1")
        if not 0 <= self.overlay_alpha <= 1.0:
            raise ValueError("overlay_alpha must be between 0 and 1")


# Global default settings instance
DEFAULT_SETTINGS = AppSettings()
