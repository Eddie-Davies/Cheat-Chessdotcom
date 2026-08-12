"""
Unit tests for main application module.
"""

from chess_analyser.main import main


def test_main_runs_without_error(capsys):
    """Test that main() runs without raising an exception."""
    main()
    captured = capsys.readouterr()
    assert "initialized successfully" in captured.out or "Phase 0" in captured.out
