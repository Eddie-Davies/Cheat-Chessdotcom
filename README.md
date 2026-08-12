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

## License

MIT License
