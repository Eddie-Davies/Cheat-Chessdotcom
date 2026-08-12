"""Formatting helpers for the main window's analysis and status fields."""

from __future__ import annotations


def format_evaluation(score: float | None, mate: int | None) -> str:
	"""Format a White-perspective engine evaluation for display."""
	if mate is not None:
		return f"Mate in {mate}" if mate > 0 else f"Mate in {abs(mate)} (black)"
	if score is None:
		return "-"
	return f"{score:+.2f}"


def format_line(score: float | None, mate: int | None) -> str:
	"""Format the evaluation portion of an alternative line."""
	return format_evaluation(score, mate)
