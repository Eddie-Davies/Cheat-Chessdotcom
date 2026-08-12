"""Unit tests for the Phase 2 chess position layer."""

import chess
import pytest

from chess_analyser.chess import (
    ChessPosition,
    PositionValidationError,
    board_to_fen,
    is_valid_fen,
)


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
EN_PASSANT_FEN = "rnbqkbnr/pppp1ppp/8/3Pp3/8/8/PPP1PPPP/RNBQKBNR w KQkq e6 0 2"


def test_starting_position_and_fen_round_trip():
    position = ChessPosition.starting()

    assert position.fen == STARTING_FEN
    assert position.is_valid()
    assert position.history == (position.position_key(),)
    assert board_to_fen(position.board) == STARTING_FEN


def test_create_position_from_piece_data():
    position = ChessPosition.from_pieces(
        {
            "a8": "black_rook",
            "e8": "black_king",
            "e1": "white_king",
            "e2": "white_pawn",
        },
        side_to_move=chess.WHITE,
    )

    assert position.board.piece_at(chess.E2) == chess.Piece.from_symbol("P")
    assert position.board.piece_at(chess.E8) == chess.Piece.from_symbol("k")
    assert position.board.turn == chess.WHITE
    assert position.board.board_fen() == "r3k3/8/8/8/8/8/4P3/4K3"


def test_normal_fen_and_side_to_move_are_preserved():
    fen = "8/8/8/3k4/8/8/4K3/8 b - - 4 22"
    position = ChessPosition.from_fen(fen)

    assert position.fen == fen
    assert position.board.turn == chess.BLACK
    assert position.is_valid()


def test_castling_rights_are_part_of_position_identity():
    with_rights = ChessPosition.from_fen(CASTLING_FEN)
    without_rights = ChessPosition.from_fen(CASTLING_FEN.replace("KQkq", "-"))

    assert with_rights.board.castling_xfen() == "KQkq"
    assert with_rights != without_rights
    assert with_rights.has_changed(without_rights)
    assert with_rights.position_hash() != without_rights.position_hash()


def test_en_passant_is_preserved_and_part_of_position_identity():
    position = ChessPosition.from_fen(EN_PASSANT_FEN)
    without_target = ChessPosition.from_fen(EN_PASSANT_FEN.replace("e6", "-"))

    assert position.board.ep_square == chess.E6
    assert position.position_key()[-1] == "e6"
    assert position != without_target


def test_position_hash_is_stable_for_equal_positions():
    first = ChessPosition.from_fen(STARTING_FEN)
    second = ChessPosition.from_fen(STARTING_FEN)

    assert first == second
    assert first.position_key() == second.position_key()
    assert first.position_hash() == second.position_hash()


def test_history_records_observed_positions():
    position = ChessPosition.starting()
    initial_key = position.position_key()
    changed_key = position.push_uci("e2e4")

    assert changed_key == position.position_key()
    assert position.history == (initial_key, changed_key)
    assert len(position.history) == 2

    position.push_san("e5")
    assert len(position.history) == 3


def test_position_change_detection_ignores_move_clock_only():
    first = ChessPosition.from_fen(STARTING_FEN)
    second = ChessPosition.from_fen(STARTING_FEN.replace("0 1", "7 15"))
    changed = ChessPosition.from_fen(STARTING_FEN.replace("w KQkq", "b KQkq"))

    assert first == second
    assert not first.has_changed(second)
    assert first.has_changed(changed)


def test_legal_moves_are_uci_and_include_starting_moves():
    position = ChessPosition.starting()

    legal_moves = position.legal_moves()

    assert len(legal_moves) == 20
    assert "e2e4" in legal_moves
    assert "g1f3" in legal_moves
    assert legal_moves == sorted(legal_moves)


def test_illegal_position_is_reported():
    position = ChessPosition.from_pieces(
        {
            "e1": "white_king",
            "e8": "black_king",
            "a2": "white_pawn",
            "b2": "white_pawn",
            "c2": "white_pawn",
            "d2": "white_pawn",
            "e2": "white_pawn",
            "f2": "white_pawn",
            "g2": "white_pawn",
            "h2": "white_pawn",
            "a3": "white_pawn",
        }
    )

    assert not position.is_valid()
    with pytest.raises(PositionValidationError, match="Invalid chess position"):
        position.validate()


def test_invalid_fen_and_piece_data_are_rejected():
    with pytest.raises(ValueError, match="Invalid FEN"):
        ChessPosition.from_fen("not a fen")

    with pytest.raises(PositionValidationError, match="Invalid piece data"):
        ChessPosition.from_pieces({"z9": "white_king"})


def test_fen_validity_helper_distinguishes_legal_positions():
    assert is_valid_fen(STARTING_FEN)
    assert not is_valid_fen("8/8/8/8/8/8/8/8 w - - 0 1")


def test_uci_and_san_move_conversion():
    position = ChessPosition.starting()

    assert position.uci_to_san("e2e4") == "e4"
    assert position.san_to_uci("e4") == "e2e4"

    with pytest.raises(ValueError, match="Illegal UCI move"):
        position.uci_to_san("e2e5")
    with pytest.raises(ValueError, match="Invalid or illegal SAN"):
        position.san_to_uci("Qh5")


def test_castling_and_en_passant_move_conversion():
    castling = ChessPosition.from_fen(CASTLING_FEN)
    en_passant = ChessPosition.from_fen(EN_PASSANT_FEN)

    assert castling.uci_to_san("e1g1") == "O-O"
    assert castling.san_to_uci("O-O-O") == "e1c1"
    assert en_passant.uci_to_san("d5e6") == "dxe6"