"""Tests for Phase 12 temporal position stability."""

import pytest

from chess_analyser.chess import ChessPosition, PositionDetection
from chess_analyser.pipeline import PositionTracker


FEN_A = "8/8/8/8/8/8/4P3/4K2k w - - 0 1"
FEN_B = "8/8/8/4p3/8/8/8/K6k b - - 0 1"


def position_a():
	return ChessPosition.from_fen(FEN_A)


def position_b():
	return ChessPosition.from_fen(FEN_B)


def test_position_becomes_stable_after_configured_frames():
	tracker = PositionTracker(stability_frames=3)

	first = tracker.update(position_a(), timestamp=0.0)
	second = tracker.update(position_a(), timestamp=0.1)
	third = tracker.update(position_a(), timestamp=0.2)

	assert not first.stable
	assert not second.stable
	assert third.stable
	assert third.frame_count == 3
	assert third.should_analyse
	assert tracker.stable_hash == third.position_hash


def test_transition_resets_confirmation_until_new_position_repeats():
	tracker = PositionTracker(stability_frames=3)
	for timestamp in (0.0, 0.1, 0.2):
		tracker.update(position_a(), timestamp=timestamp)
	a_hash = tracker.stable_hash

	transition = tracker.update(position_b(), timestamp=0.3)
	second_b = tracker.update(position_b(), timestamp=0.4)
	stable_b = tracker.update(position_b(), timestamp=0.5)

	assert transition.transition
	assert not transition.stable
	assert transition.frame_count == 1
	assert not second_b.stable
	assert stable_b.stable
	assert stable_b.should_analyse
	assert stable_b.position_hash != a_hash
	assert tracker.stable_hash == stable_b.position_hash


def test_concrete_board_state_change_only_analyses_settled_new_position():
	tracker = PositionTracker(stability_frames=3)
	starting = ChessPosition.starting()
	after_move = ChessPosition.starting()
	after_move.push_uci("e2e4")

	frames = [starting, starting, starting, after_move, after_move, after_move, after_move]
	updates = [tracker.update(position, timestamp=index * 0.1) for index, position in enumerate(frames)]

	assert [update.should_analyse for update in updates] == [False, False, True, False, False, True, False]
	assert updates[3].transition
	assert not updates[3].stable
	assert updates[5].stable
	assert updates[5].position.fen == after_move.fen


def test_transient_position_does_not_trigger_analysis():
	tracker = PositionTracker(stability_frames=3)

	updates = [
		tracker.update(position_a(), timestamp=0.0),
		tracker.update(position_b(), timestamp=0.1),
		tracker.update(position_a(), timestamp=0.2),
		tracker.update(position_b(), timestamp=0.3),
	]

	assert all(not update.stable for update in updates)
	assert all(not update.should_analyse for update in updates)


def test_debounce_delay_is_required_in_addition_to_frame_count():
	tracker = PositionTracker(stability_frames=2, debounce_ms=500)

	first = tracker.update(position_a(), timestamp=0.0)
	second = tracker.update(position_a(), timestamp=0.1)
	third = tracker.update(position_a(), timestamp=0.5)

	assert not first.stable
	assert not second.stable
	assert third.stable
	assert third.should_analyse


def test_same_stable_hash_does_not_request_duplicate_analysis():
	tracker = PositionTracker(stability_frames=2)

	first_stable = tracker.update(position_a(), timestamp=0.0)
	second_stable = tracker.update(position_a(), timestamp=0.1)
	later = tracker.update(position_a(), timestamp=0.2)

	assert not first_stable.should_analyse
	assert second_stable.should_analyse
	assert later.stable
	assert not later.should_analyse


def test_returning_to_previously_analysed_position_is_cached():
	tracker = PositionTracker(stability_frames=2)
	tracker.update(position_a(), timestamp=0.0)
	a_stable = tracker.update(position_a(), timestamp=0.1)
	tracker.update(position_b(), timestamp=0.2)
	tracker.update(position_b(), timestamp=0.3)
	tracker.update(position_a(), timestamp=0.4)
	a_again = tracker.update(position_a(), timestamp=0.5)

	assert a_stable.should_analyse
	assert a_again.stable
	assert not a_again.should_analyse


def test_accepts_reconstructed_position_detection():
	position = position_a()
	detection = PositionDetection(
		pieces={"e1": "white_king", "h1": "black_king", "e2": "white_pawn"},
		side_to_move="white",
		fen=position.fen,
		confidence=0.9,
		stable=True,
		position=position,
	)

	update = PositionTracker(stability_frames=1).update(detection, timestamp=0.0)

	assert update.stable
	assert update.should_analyse


def test_invalid_input_and_configuration_are_rejected():
	with pytest.raises(ValueError):
		PositionTracker(stability_frames=0)
	with pytest.raises(ValueError):
		PositionTracker(debounce_ms=-1)
	with pytest.raises(TypeError):
		PositionTracker().update("not a position", timestamp=0.0)


def test_reset_allows_position_to_be_analysed_again():
	tracker = PositionTracker(stability_frames=1)
	first = tracker.update(position_a(), timestamp=0.0)
	tracker.reset()
	second = tracker.update(position_a(), timestamp=1.0)

	assert first.should_analyse
	assert second.should_analyse
	assert tracker.candidate_frames == 1