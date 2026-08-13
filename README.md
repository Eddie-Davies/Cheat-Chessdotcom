# Chess Analyser

A cross-platform Python desktop application that automatically detects chessboards, analyzes positions with Stockfish, and displays real-time analysis through a transparent overlay.

## Features (Planned)

- **Automatic Board Detection**: Detects chessboards anywhere on your screen without manual configuration
- **Piece Recognition**: Automatically identifies all chess pieces and their positions
- **Stockfish Analysis**: Analyzes positions with the Stockfish engine
- **Real-time Overlay**: Displays the best move and candidate moves directly on the board
- **Position Tracking**: Automatically re-analyzes when the position changes
- **Global Hotkey**: Hide/show overlay with a keyboard shortcut to interact with your chess application
- **Cross-platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.12+
- Stockfish chess engine
- Tkinter (usually included with Python)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python -m chess_analyser
```

## Development

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/chess_analyser
```

## Project Status

Phase 13 is implemented. The near-term testing target is the green
Chess.com board theme used during play.

Green-board screenshot regression tests should use fixtures under:

```text
assets/test_screens/chesscom_standard_start/
assets/test_screens/chesscom_green_active_game/
```

Wood and brown boards remain explicitly deferred for later improvement:
piece recognition needs additional templates, and board-boundary detection
is currently slightly offset or partial on some of those fixtures.

Save a diagnostic screenshot with:

```bash
python -m chess_analyser.capture.screen_capture
```

Use `--output path/to/capture.png` to choose another output path.

Annotate a screenshot with the detected board boundary and grid:

```bash
python -m chess_analyser.detection.board_detector \
   assets/test_screens/capture_phase4.png \
   assets/test_screens/detected_phase5.png
```

Label the mapped chess squares after detection:

```bash
python -m chess_analyser.detection.square_detector \
   assets/test_screens/chess_com_board_01.png \
   assets/test_screens/squares_phase6_chesscom.png \
   --x 247 --y 152 --width 928 --height 928 \
   --orientation white_bottom
```

Phase 7 orientation detection combines optional board-label observations,
recognized corner-piece hints, and previous orientation history. It returns
`white_bottom`, `black_bottom`, or `unknown` with a confidence score. Raw
label OCR and full piece recognition remain separate later capabilities.

Phase 8 occupancy detection classifies each mapped square as `occupied`,
`empty`, or `uncertain` using local background estimation, foreground color
distance, connected silhouette area, and edge density.

Phase 9 adds the replaceable `PieceDetector` interface and a deterministic
`TemplatePieceDetector`. It recognizes the observed Chess.com piece set
using normalized silhouette templates and confidence scores. The current
templates are representative only and are not universal across chess sites.

Generate a piece-recognition diagnostic image with:

```bash
python -m chess_analyser.detection.piece_detector \
   assets/test_screens/chess_com_board_01.png \
   assets/test_screens/occupancy_phase8_chesscom.png \
   --x 247 --y 152 --width 928 --height 928
```

Templates are stored under [assets/piece_templates](assets/piece_templates).

Phase 10 `PositionReconstructor` consumes the orientation-corrected piece
map and existing occupancy results, requires exactly one white king and one
black king, validates the resulting `ChessPosition`, and returns a FEN plus
confidence. Invalid or low-confidence detections raise an explicit error;
they are never silently passed to the engine.

Phase 11 `SideToMoveDetector` combines active-player indicators, board
highlights, active clocks, UI indicators, and confirmed history. It returns
`white`, `black`, or `unknown` with confidence. `PositionReconstructor`
rejects an unknown side rather than assuming White to move.

Phase 12 `PositionTracker` confirms a reconstructed position only after the
configured number of consecutive matching hashes and optional debounce
delay. A changed hash enters transition state, and each stable hash emits at
most one analysis request until the tracker is reset. Transient animation
frames therefore do not trigger analysis.

Phase 13 `AutomaticAnalysisPipeline` connects capture, board detection,
square mapping, orientation, occupancy, piece recognition, reconstruction,
side-to-move, stability, and engine analysis. It exposes explicit states such
as `SEARCHING`, `POSITION_UNCERTAIN`, `POSITION_STABLE`, `ANALYSING`,
`ANALYSIS_READY`, and `ERROR`, runs continuous work on a background thread,
and caches results by position hash. Overlay rendering is intentionally not
part of this phase.

## License

MIT License
