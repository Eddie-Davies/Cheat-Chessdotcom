# Phase 5 Detection Fixtures

The board detector tests use representative generated screenshots with
different board positions, sizes, and light/dark square palettes. Their
construction is in `tests/unit/test_board_detector.py` so the geometry is
explicit and reproducible without tying production code to a website.

`capture_phase4.png` is a real Windows desktop capture from Phase 4. It is
used as a negative regression fixture because it contains no chessboard; the
detector must return no result rather than treating an arbitrary desktop
rectangle as a board.

`chess_com_board_01.png` is a real Chess.com positive fixture. The detector
identifies its colored 8x8 board area at approximately `(247, 152)` with a
`928x928` footprint and high confidence. Precise square mapping is
intentionally deferred to Phase 6.