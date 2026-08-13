# Chess.com Screenshot Batch Report

Each fixture folder contains the raw source screenshot and, when automatic board detection succeeded, the generated annotations beside it.

## Annotation Files

- `board_detection.png`: detected board bounding box and confidence
- `square_labels_white_bottom.png`: mapped algebraic square labels
- `occupancy.png`: green occupied / gray empty / yellow uncertain
- `piece_recognition.png`: recognized piece names and confidence

## Results

| Folder | Board detection | Confidence | Board bounds | Occupied | Pieces | Piece confidence >= 0.55 |
|---|---|---:|---|---:|---:|---:|
| `chesscom_standard_start` | PASS | 0.863 | `(247, 152) 928x928` | 32 | 32 | 32 |
| `chesscom_green_active_game` | PASS | 0.855 | `(68, 50) 348x348` | 30 | 30 | 12 |
| `chesscom_wood_variant` | PASS, likely partial/incorrect scale | 0.632 | `(284, 134) 440x440` | 24 | 24 | 3 |
| `chesscom_brown_tactical` | PASS, likely partial/incorrect scale | 0.632 | `(284, 134) 440x440` | 24 | 24 | 3 |
| `chesscom_green_large_game` | FAIL | n/a | Board not detected | n/a | n/a | n/a |
| `chesscom_wood_start` | FAIL | n/a | Board not detected | n/a | n/a | n/a |
| `reference_non_board` | PASS rejection | n/a | No board returned | n/a | n/a | n/a |

## Interpretation

The active acceptance target is now the green Chess.com theme:
`chesscom_standard_start` and `chesscom_green_active_game`. Future real
screenshot tests should use green-board fixtures only.

The standard Chess.com fixture is fully successful: the board is detected, all 32 occupied squares are recognized, and the templates match the observed starting position.

The green active-game screenshot is detected and occupancy works, but the current template set is not reliable enough for that visual state. Its piece annotations are included to show the failure pattern rather than hide it.

The brown/wood variants produce low-confidence partial detections. Their annotations are intentionally omitted from the final folders because they could be misleading as board-level ground truth. The raw screenshots remain available for detector improvement.

The large green game and wooden starting board are currently board-detection failures. No fabricated square or piece annotations were generated for them.

`reference_non_board/desktop_no_board.png` remains a negative fixture and correctly returns no board.

## Important Limitations

- The current board detector is deterministic and has not yet been tuned for every Chess.com theme or layout.
- The current template set targets the original standard Chess.com piece appearance.
- Green-board screenshots are the active near-term testing target.
- Wood/brown piece recognition and board-boundary precision are explicitly deferred follow-up work.
- Orientation and side-to-move extraction still require structured evidence; raw screenshot OCR/UI extraction is not complete.
- These results are concrete fixture results, not a claim of universal site support.
