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

Phase 4 complete: the diagnostic Tkinter interface can accept a FEN and
run asynchronous engine analysis without blocking the GUI, and the
cross-platform MSS capture API can save diagnostic screenshots. Automatic
board detection, piece recognition, and overlays remain future phases.

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
distance, connected silhouette area, and edge density. It does not identify
piece types. A diagnostic image can be generated with:

```bash
python -m chess_analyser.detection.piece_detector \
   assets/test_screens/chess_com_board_01.png \
   assets/test_screens/occupancy_phase8_chesscom.png \
   --x 247 --y 152 --width 928 --height 928
```

## License

MIT License
