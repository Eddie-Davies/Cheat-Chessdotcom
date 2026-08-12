# AGENTS.md --- Chess Analyser Project

## 1. Purpose

You are an AI coding agent working on the **Chess Analyser** project.

Your job is to incrementally build a **cross-platform Python desktop application targeting Windows, macOS, and Linux**
that:

1.  Captures the user's screen.
2.  Automatically detects a chessboard without requiring manual
    coordinates.
3.  Determines the board's orientation.
4.  Detects the pieces on the board automatically.
5.  Reconstructs the chess position.
6.  Converts the position into a representation usable by
    `python-chess`.
7.  Analyses the position using Stockfish.
8.  Produces the strongest move and several candidate moves.
9.  Displays the analysis through a transparent visual overlay aligned
    with the detected board.
10. Automatically notices when the position changes and re-analyses it.
11. Lets the user hide/show the overlay with a global hotkey so the
    underlying chess application can be interacted with normally.

The final system should require **as little user configuration as
possible**.

The intended final workflow is:

``` text
Launch application
       ↓
Capture screen
       ↓
Automatically find chessboard
       ↓
Determine board geometry/orientation
       ↓
Detect pieces
       ↓
Validate position
       ↓
Build chess position
       ↓
Analyse with Stockfish
       ↓
Render suggested move
       ↓
Monitor for position changes
       ↓
Repeat
```

The application must never automatically make a chess move or inject
mouse/keyboard actions into the underlying chess application.

------------------------------------------------------------------------

# 2. Source of Truth

This file is the primary development instruction for AI coding agents.

Before making changes:

1.  Read this file completely.
2.  Inspect the existing repository.
3.  Determine which phase the project is currently in.
4.  Do not skip phases unless the user explicitly asks.
5.  Do not replace working architecture with a new architecture without
    a clear reason.
6.  Preserve existing working functionality when adding new
    functionality.

If another project document exists, such as `PROJECT_SPEC.md`, use it as
supplementary documentation. If there is a conflict, prefer explicit
user instructions, then this `AGENTS.md`, then the project
specification.

------------------------------------------------------------------------

# 3. Core Development Rules

## 3.1 Build incrementally

Do not attempt to implement the entire project in one pass.

Work in small, testable increments.

Each phase must have:

-   implementation,
-   tests,
-   a working demonstration,
-   documented limitations.

Only proceed when the current phase's acceptance criteria are met.

## 3.2 Keep components separate

Do not put the entire application into `main.py`.

Use separate modules for:

-   screen capture,
-   board detection,
-   square detection,
-   orientation detection,
-   piece recognition,
-   chess position management,
-   Stockfish,
-   overlay rendering,
-   application UI,
-   configuration.

## 3.3 Do not hardcode a specific chess website

Never hardcode coordinates such as:

``` python
board_x = 500
board_y = 100
board_size = 800
```

The final application must find the board automatically.

Test fixtures may contain fixed coordinates, but production code must
not depend on them.

## 3.4 Do not require manual FEN entry in the final system

FEN input can exist as a diagnostic/development feature, but it must not
be required for normal operation.

## 3.5 Do not require manual board positioning in the final system

Manual calibration may exist as a fallback/debugging mode, but automatic
detection is the primary path.

## 3.6 Never make moves

The application is an analysis/learning tool.

It must not:

-   click chess squares,
-   send moves,
-   submit moves,
-   press game controls,
-   interact with the underlying chess application on the user's behalf.

The overlay is informational only.

## 3.7 Avoid unnecessary dependencies

Prefer standard Python libraries and well-established packages.

Recommended initial dependencies:

-   `python-chess`
-   `stockfish` executable
-   `mss`
-   `opencv-python`
-   `numpy`
-   `Pillow`
-   a global-hotkey library suitable for Windows

Only add a dependency when there is a clear reason.

## 3.8 Do not introduce machine learning prematurely

Start with deterministic computer vision and template-based approaches.

Only introduce a trained classifier if the simpler system cannot achieve
acceptable reliability.

The piece-recognition interface must be designed so that the
implementation can later be replaced.

------------------------------------------------------------------------

# 4. Technology Stack

## Required

-   Python 3.12
-   Windows
-   VS Code
-   Git
-   `python-chess`
-   Stockfish
-   Tkinter

## Recommended

-   `mss` --- screen capture
-   OpenCV --- computer vision
-   NumPy --- image/data processing
-   Pillow --- image handling
-   `pytest` --- testing

The exact hotkey library can be selected during implementation after
evaluating Windows compatibility.

------------------------------------------------------------------------

# 5. Target Architecture

Use the following conceptual architecture:

``` text
                    ┌──────────────────────┐
                    │      Screen          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Screen Capture     │
                    │        MSS           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Board Detector     │
                    │       OpenCV         │
                    └──────────┬───────────┘
                               │
                    board geometry/orientation
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Square Detector    │
                    └──────────┬───────────┘
                               │
                          64 squares
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Piece Detector     │
                    └──────────┬───────────┘
                               │
                         piece positions
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Position Manager     │
                    │    python-chess      │
                    └──────────┬───────────┘
                               │
                              FEN
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Stockfish       │
                    └──────────┬───────────┘
                               │
                    best move / PV / score
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Overlay Renderer   │
                    │       Tkinter        │
                    └──────────┬───────────┘
                               │
                               ▼
                         Screen overlay
```

------------------------------------------------------------------------

# 6. Repository Structure

Use this structure unless there is a strong technical reason to change
it:

``` text
ChessAnalyser/
│
├── AGENTS.md
├── README.md
├── PROJECT_SPEC.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── src/
│   └── chess_analyser/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py
│       │
│       ├── capture/
│       │   ├── __init__.py
│       │   └── screen_capture.py
│       │
│       ├── detection/
│       │   ├── __init__.py
│       │   ├── board_detector.py
│       │   ├── square_detector.py
│       │   ├── orientation.py
│       │   └── piece_detector.py
│       │
│       ├── chess/
│       │   ├── __init__.py
│       │   ├── position.py
│       │   ├── fen.py
│       │   └── moves.py
│       │
│       ├── engine/
│       │   ├── __init__.py
│       │   └── stockfish_engine.py
│       │
│       ├── overlay/
│       │   ├── __init__.py
│       │   ├── overlay_window.py
│       │   ├── arrows.py
│       │   └── highlights.py
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   └── status.py
│       │
│       └── pipeline/
│           ├── __init__.py
│           ├── detector.py
│           ├── position_tracker.py
│           └── analyser.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── assets/
│   ├── piece_templates/
│   └── test_screens/
│
└── engine/
    └── stockfish/
        ├── windows/
        ├── macos/
        └── linux/
```

Keep source code under `src/`.

------------------------------------------------------------------------

# 7. Data Models

Create explicit data models rather than passing loose dictionaries
everywhere.

Use Python `dataclasses` where appropriate.

## BoardDetection

Conceptually:

``` python
@dataclass
class BoardDetection:
    x: int
    y: int
    width: int
    height: int
    square_size: float
    orientation: str
    confidence: float
```

Possible orientation values:

``` text
white_bottom
black_bottom
unknown
```

## SquareDetection

Represent a screen-space square:

``` python
@dataclass
class SquareDetection:
    square: str
    x: int
    y: int
    width: int
    height: int
    image: ...
```

## PieceDetection

``` python
@dataclass
class PieceDetection:
    square: str
    piece: str
    confidence: float
```

Piece values should use a consistent internal representation, for
example:

``` text
white_pawn
white_knight
white_bishop
white_rook
white_queen
white_king

black_pawn
black_knight
black_bishop
black_rook
black_queen
black_king
```

## PositionDetection

``` python
@dataclass
class PositionDetection:
    pieces: dict[str, str]
    side_to_move: str | None
    fen: str | None
    confidence: float
    stable: bool
```

## EngineAnalysis

``` python
@dataclass
class EngineLine:
    move: str
    san: str
    score: float | None
    mate: int | None
    depth: int
    principal_variation: list[str]
```

``` python
@dataclass
class EngineAnalysis:
    best_move: str
    best_move_san: str
    score: float | None
    mate: int | None
    depth: int
    lines: list[EngineLine]
```

------------------------------------------------------------------------

# 8. Required Component Interfaces

The exact implementation can vary, but the following conceptual
interfaces should remain stable.

## Screen capture

``` python
screen = screen_capture.capture()
```

It should return an image object suitable for OpenCV processing.

It should also support:

``` python
screen_capture.capture_region(x, y, width, height)
```

for performance optimisation after the board has been found.

## Board detection

``` python
result = board_detector.detect(screen)
```

Return:

``` text
BoardDetection | None
```

The detector must include confidence.

## Piece detection

``` python
result = piece_detector.detect(board_image, board_detection)
```

Return a `PositionDetection` or a collection of `PieceDetection`
objects.

## Engine

``` python
analysis = engine.analyse(position, depth=20, multipv=5)
```

The engine module must hide the details of the UCI protocol.

## Overlay

``` python
overlay.show()
overlay.hide()
overlay.update(board_detection, analysis)
```

The overlay must not know how Stockfish works.

## Pipeline

The pipeline coordinates everything:

``` python
pipeline.start()
pipeline.stop()
```

It should own the detection/analyse loop.

------------------------------------------------------------------------

# 9. Development Order

This order is mandatory unless a technical issue requires deviation.

------------------------------------------------------------------------

# PHASE 0 --- Repository Setup

## Objective

Create a clean Python project.

## Tasks

-   Create repository.
-   Create virtual environment.
-   Create `src` layout.
-   Create `tests`.
-   Create `.gitignore`.
-   Create `requirements.txt`.
-   Create `pyproject.toml`.
-   Configure VS Code Python interpreter.
-   Configure pytest.
-   Add basic logging.

## Acceptance criteria

-   `python --version` works.
-   Virtual environment activates.
-   `pytest` runs.
-   Project imports successfully.
-   `python -m ...` can start the application.
-   Git repository is clean and structured.

Do not begin computer vision yet.

------------------------------------------------------------------------

# PHASE 1 --- Stockfish Integration

## Objective

Get a completely reliable chess engine subsystem.

## Tasks

1.  Add Stockfish executable.
2.  Implement engine startup.
3.  Implement engine shutdown.
4.  Implement FEN analysis.
5.  Implement depth-based analysis.
6.  Implement time-based analysis.
7.  Implement MultiPV.
8.  Convert UCI moves to SAN.
9.  Normalise evaluations.
10. Handle mate scores.
11. Add error handling.
12. Add tests.

## Example

Input:

``` text
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

Expected output should contain:

``` text
best move
evaluation
depth
principal variation
```

## Acceptance criteria

-   Stockfish starts.
-   Stockfish shuts down cleanly.
-   FEN can be analysed.
-   Best move is returned.
-   MultiPV works.
-   Depth works.
-   Time limit works.
-   Mate scores are handled.
-   Invalid FEN produces a useful error.
-   Unit tests pass.

Do not proceed until this is stable.

------------------------------------------------------------------------

# PHASE 2 --- Chess Position Layer

## Objective

Create a reliable internal representation of chess positions.

## Tasks

-   Create position model.
-   Integrate `python-chess`.
-   Convert piece maps to `chess.Board`.
-   Generate FEN.
-   Validate legal positions.
-   Convert UCI to SAN.
-   Track position hashes.
-   Track position history.
-   Add tests.

## Acceptance criteria

Given:

``` text
a8 = black_rook
e8 = black_king
e1 = white_king
e2 = white_pawn
```

the system can construct a valid chess board where possible.

It must:

-   generate FEN,
-   validate the board,
-   identify legal moves,
-   detect whether two positions are identical.

------------------------------------------------------------------------

# PHASE 3 --- Basic Tkinter UI

## Objective

Build a basic application shell.

## UI requirements

Show:

``` text
CHESS ANALYSER

Engine:
  Stockfish

Depth:
  [20]

Lines:
  [5]

Time:
  [1.0s]

Position:
  [diagnostic FEN field]

Best move:
  Nf3

Evaluation:
  +0.42

Alternatives:
  d4
  Bc4
  Nc3

Status:
  Ready
```

## Tasks

-   Create main window.
-   Add engine settings.
-   Add analysis display.
-   Add status indicator.
-   Add diagnostic FEN input.
-   Add Analyse button.
-   Keep engine analysis off the UI thread.

The FEN field is only a development/diagnostic feature.

## Acceptance criteria

A user can paste a FEN and receive engine analysis without freezing the
UI.

------------------------------------------------------------------------

# PHASE 4 --- Screen Capture

## Objective

Capture the screen efficiently.

## Tasks

-   Integrate `mss`.
-   Capture monitor.
-   Capture region.
-   Add configurable capture frequency.
-   Add diagnostic screenshot saving.
-   Add logging.

Create a diagnostic command that saves:

``` text
assets/test_screens/capture_YYYYMMDD_HHMMSS.png
```

## Acceptance criteria

-   Application can capture the screen.
-   Capture does not freeze the UI.
-   Captured images can be processed by OpenCV.
-   Diagnostic images can be saved.

------------------------------------------------------------------------

# PHASE 5 --- Automatic Board Detection

## Objective

Automatically locate an 8×8 chessboard on the screen.

This is the first major computer-vision phase.

## Requirements

Do not depend on:

-   fixed coordinates,
-   fixed board size,
-   one specific board colour,
-   one specific chess piece set.

## Detection strategy

Start with deterministic vision.

Potential pipeline:

``` text
screen
 ↓
resize/downsample if useful
 ↓
candidate square regions
 ↓
square/rectangle detection
 ↓
colour-pattern analysis
 ↓
8×8 regularity test
 ↓
board candidate scoring
 ↓
best candidate
```

## Board candidate scoring

Consider:

-   aspect ratio close to 1:1,
-   regular 8×8 structure,
-   alternating square colours,
-   consistent square size,
-   strong internal grid/colour transitions,
-   sufficient size,
-   confidence.

## Acceptance criteria

Given a test screenshot containing a chessboard:

-   board is detected,
-   bounding rectangle is correct within a small tolerance,
-   square size is calculated,
-   confidence is returned,
-   false positives are rejected where possible.

Create a test suite with several screenshots.

------------------------------------------------------------------------

# PHASE 6 --- Square Mapping

## Objective

Convert board geometry into the 64 chess squares.

Given:

``` text
x
y
width
height
orientation
```

calculate the screen rectangle for:

``` text
a8 ... h8
...
a1 ... h1
```

## Acceptance criteria

For known test boards:

-   all 64 squares are generated,
-   each square has correct screen coordinates,
-   orientation is handled correctly,
-   mapping is reversible.

Create unit tests for square coordinates.

------------------------------------------------------------------------

# PHASE 7 --- Board Orientation Detection

## Objective

Determine whether:

``` text
White is at bottom
```

or:

``` text
Black is at bottom
```

## Detection sources

Use multiple signals where available:

1.  Board labels.
2.  Recognised pieces.
3.  Known UI patterns.
4.  Position history.
5.  Visual orientation cues.

Do not rely on one fragile signal.

## Acceptance criteria

Test both:

-   normal orientation,
-   flipped orientation.

The mapping from screen coordinates to algebraic squares must be correct
in both cases.

------------------------------------------------------------------------

# PHASE 8 --- Empty Square Detection

## Objective

Before recognising individual pieces, reliably determine whether each
square is occupied.

## Tasks

For each square:

``` text
square image
 ↓
background estimation
 ↓
foreground analysis
 ↓
occupied / empty
```

This creates:

``` text
empty
occupied
```

for all 64 squares.

## Acceptance criteria

On representative test screenshots:

-   empty squares are identified reliably,
-   pieces are not mistaken for empty squares,
-   board decorations do not cause excessive false positives.

------------------------------------------------------------------------

# PHASE 9 --- Piece Recognition

## Objective

Identify the piece and colour occupying every non-empty square.

## Initial implementation

Start with template matching or another deterministic image-recognition
technique.

Do not immediately build a neural network.

The detector must support:

``` text
white_pawn
white_knight
white_bishop
white_rook
white_queen
white_king

black_pawn
black_knight
black_bishop
black_rook
black_queen
black_king
```

## Architecture requirement

The rest of the application must not care whether recognition is:

-   template matching,
-   feature matching,
-   classical computer vision,
-   machine learning.

Only the detector interface matters.

## Confidence

Every piece prediction must include confidence.

Example:

``` text
e4 = white_pawn
confidence = 0.98
```

## Acceptance criteria

Create a representative test dataset.

The recogniser should reliably identify common positions.

Do not claim universal piece-set support until it has actually been
tested.

------------------------------------------------------------------------

# PHASE 10 --- Position Reconstruction

## Objective

Turn detected pieces into a valid chess position.

Pipeline:

``` text
64 detected squares
       ↓
piece map
       ↓
orientation correction
       ↓
python-chess board
       ↓
position validation
       ↓
FEN
```

## Validation

Reject or flag impossible positions such as:

-   missing kings,
-   too many kings,
-   impossible pawn counts,
-   obviously contradictory positions.

Do not silently feed low-confidence positions into Stockfish.

## Acceptance criteria

A recognised starting position produces the correct FEN.

Known test positions produce matching FEN piece placement.

------------------------------------------------------------------------

# PHASE 11 --- Side-to-Move Detection

## Objective

Determine whose move it is.

This cannot always be inferred from piece placement alone.

Use visible UI information where reliable.

Possible methods:

-   detect board-side highlight,
-   detect turn indicator,
-   detect clock/active-player state,
-   use position history,
-   infer from the previous known position.

## Requirements

Do not assume White to move every time.

If side-to-move confidence is insufficient, mark the position as
uncertain rather than making an unsafe assumption.

## Acceptance criteria

Test both:

-   White to move.
-   Black to move.

------------------------------------------------------------------------

# PHASE 12 --- Position Stability and Animation Handling

## Objective

Prevent the application from analysing transient animation frames.

Use temporal confirmation.

Example:

``` text
Frame 1 → Position A
Frame 2 → Position A
Frame 3 → Position A

Position A confirmed
```

When the board changes:

``` text
Frame 4 → transition
Frame 5 → transition
Frame 6 → Position B
Frame 7 → Position B
Frame 8 → Position B

Position B confirmed
```

## Requirements

-   configurable stability threshold,
-   configurable frame count,
-   debounce analysis,
-   ignore incomplete animations.

## Acceptance criteria

A moving piece does not cause repeated false engine analyses.

------------------------------------------------------------------------

# PHASE 13 --- Automatic Analysis Pipeline

## Objective

Connect everything.

``` text
SCREEN
 ↓
CAPTURE
 ↓
BOARD DETECTION
 ↓
SQUARE MAPPING
 ↓
PIECE DETECTION
 ↓
ORIENTATION
 ↓
POSITION
 ↓
VALIDATION
 ↓
STABILITY
 ↓
STOCKFISH
 ↓
ANALYSIS RESULT
```

## Requirements

-   Background worker for computer vision.
-   Background worker for engine analysis.
-   Thread-safe communication with UI.
-   Position caching.
-   No duplicate analysis.
-   Graceful error recovery.

## Acceptance criteria

A supported test screen can automatically go from image to Stockfish
analysis without manual FEN input.

------------------------------------------------------------------------

# PHASE 14 --- Transparent Overlay

## Objective

Display engine information over the detected board.

## Requirements

The overlay must:

-   be borderless,
-   have transparent background,
-   remain above the underlying window,
-   align with the detected board,
-   update when board position changes,
-   not send input to the underlying application,
-   be hideable.

## Overlay states

``` text
VISIBLE
HIDDEN
```

## Hotkey

Default:

``` text
F8
```

Behaviour:

``` text
F8 → hide overlay
F8 → show overlay
```

The exact hotkey can be configurable later.

------------------------------------------------------------------------

# PHASE 15 --- Move Arrow Rendering

## Objective

Draw the best move directly on the board.

For example:

``` text
e2 ─────────► e4
```

The arrow must be calculated from the detected board geometry.

## Requirements

Support:

-   source square,
-   destination square,
-   captures,
-   promotions,
-   alternative moves if enabled.

The first version should display only the best move.

Later:

``` text
Best move
Alternative 1
Alternative 2
```

can use different visual treatments.

------------------------------------------------------------------------

# PHASE 16 --- Evaluation Display

Add a small overlay panel containing:

``` text
BEST MOVE

Nf3

+0.42

Depth 20
```

Optionally:

``` text
1. Nf3  +0.42
2. d4   +0.35
3. Bc4  +0.28
4. Nc3  +0.21
5. O-O  +0.18
```

The panel should not obscure important board areas unnecessarily.

------------------------------------------------------------------------

# PHASE 17 --- Automatic Overlay Alignment

The overlay should automatically use:

``` text
BoardDetection.x
BoardDetection.y
BoardDetection.width
BoardDetection.height
```

No manual positioning should be required.

When the board moves or resizes:

``` text
new board detected
       ↓
overlay repositions
```

------------------------------------------------------------------------

# PHASE 18 --- Main Control Window

The control window should show:

``` text
CHESS ANALYSER

Board:
  Detected

Confidence:
  98%

Pieces:
  32/32

Position:
  Stable

Engine:
  Stockfish

Depth:
  20

Lines:
  5

Overlay:
  Visible

Hotkey:
  F8
```

Controls:

``` text
Start
Pause
Show Overlay
Hide Overlay
Re-detect Board
Engine Settings
```

Manual re-detection is a debugging/recovery feature, not normal
operation.

------------------------------------------------------------------------

# PHASE 19 --- Error Handling

The application must handle:

## Board not found

Display:

``` text
Waiting for chessboard...
```

Do not crash.

## Multiple boards found

Choose the highest-confidence candidate.

If confidence is too close between candidates, show:

``` text
Multiple chessboards detected.
```

and allow diagnostic selection.

## Piece recognition failure

Display:

``` text
Position uncertain.
```

Do not analyse a low-confidence position.

## Invalid position

Display:

``` text
Invalid chess position detected.
```

## Stockfish unavailable

Display:

``` text
Stockfish unavailable.
```

Do not crash.

## Overlay failure

The analyser must continue running even if the overlay needs to be
restarted.

------------------------------------------------------------------------

# PHASE 20 --- Testing

Testing is required throughout development.

## Unit tests

Test:

-   FEN handling,
-   position construction,
-   square mapping,
-   orientation,
-   coordinate calculations,
-   engine parsing,
-   evaluation conversion,
-   position hashing.

## Computer vision tests

Create fixture screenshots covering:

-   normal board,
-   flipped board,
-   different sizes,
-   different screen positions,
-   light board themes,
-   dark board themes,
-   different piece sets,
-   partially obstructed boards where relevant.

## Integration tests

Test:

``` text
image → board → pieces → position → engine
```

without requiring the GUI.

## Regression tests

Every bug discovered in board/piece detection should result in a saved
fixture and a regression test where practical.

------------------------------------------------------------------------

# 21. Diagnostic Mode

The application should have a developer/debug mode.

It should be able to display:

``` text
Board confidence: 0.98
Orientation: white_bottom
Square size: 100.2
Piece confidence: 0.96
Position stable: yes
FEN: ...
```

And optionally draw:

-   board bounding box,
-   square grid,
-   square labels,
-   detected piece names,
-   confidence values.

Example:

``` text
┌───────────────────────────┐
│ a8  b8  c8  d8  e8 ...  │
│                           │
│      [black knight]       │
│         0.98              │
│                           │
└───────────────────────────┘
```

This mode is extremely important for debugging computer vision.

------------------------------------------------------------------------

# 22. Logging

Use Python's `logging` module.

Levels:

-   DEBUG
-   INFO
-   WARNING
-   ERROR

Do not use `print()` for application diagnostics once the basic
prototype is working.

Log useful events:

``` text
Board detected
Board lost
Orientation changed
Position changed
Position stabilised
Engine analysis started
Engine analysis completed
Overlay shown
Overlay hidden
Piece recognition failed
```

Avoid logging huge image data.

------------------------------------------------------------------------

# 23. Performance Targets

The application should eventually aim for:

-   low idle CPU usage,
-   responsive GUI,
-   fast board detection,
-   fast position recognition,
-   no unnecessary Stockfish calls.

Optimisations should be introduced only after correctness.

Potential optimisation sequence:

``` text
Full-screen capture
       ↓
Detect board
       ↓
Capture only board region
       ↓
Detect squares
       ↓
Track board location
       ↓
Only re-run full detection when board is lost
```

Do not prematurely optimise before correctness is established.

------------------------------------------------------------------------

# 24. Position Caching

Use a position hash.

Example:

``` python
position_key = (
    board_piece_placement,
    side_to_move,
    castling_rights,
    en_passant_square,
)
```

If the same position appears again, cached engine analysis can be
reused.

Cache should be bounded so memory does not grow indefinitely.

------------------------------------------------------------------------

# 25. Threading and Concurrency

Tkinter must remain on the main thread.

Do not perform:

-   screen capture loops,
-   OpenCV processing,
-   Stockfish analysis

directly in Tkinter callbacks if they can block.

Use worker threads or an appropriate concurrency design.

Conceptually:

``` text
Tkinter main thread
       │
       ├── UI
       └── Overlay

Detection worker
       │
       └── Screen/CV

Engine worker
       │
       └── Stockfish
```

Use queues/events for communication.

Do not directly manipulate Tkinter widgets from worker threads.

------------------------------------------------------------------------

# 26. Configuration

Create a central configuration model.

Potential settings:

``` text
engine_path
engine_depth
engine_time
multipv
capture_interval
board_detection_interval
position_stability_frames
piece_confidence_threshold
board_confidence_threshold
overlay_hotkey
overlay_alpha
show_evaluation
show_alternatives
debug_mode
```

Do not scatter constants throughout the code.

------------------------------------------------------------------------

# 27. UI/UX Principles

The final application should be simple.

The user should not need to understand:

-   FEN,
-   UCI,
-   OpenCV,
-   Stockfish,
-   computer vision.

Normal state:

``` text
Board detected ✓
Position stable ✓
Analysing...
```

If something goes wrong:

``` text
Chessboard not detected
```

rather than a Python traceback.

Detailed diagnostics belong in logs/debug mode.

------------------------------------------------------------------------

# 28. Development Workflow for AI Agents

When asked to implement a feature:

1.  Read `AGENTS.md`.
2.  Inspect existing code.
3.  Identify the current phase.
4.  Identify dependencies.
5.  Make the smallest coherent change.
6.  Add/update tests.
7.  Run tests.
8.  Fix failures.
9.  Run formatting/linting if configured.
10. Update documentation if behaviour changed.
11. Report exactly what changed.

Do not silently skip tests.

Do not claim functionality is complete if it has not been tested.

------------------------------------------------------------------------

# 29. How to Handle Uncertainty

If a technical decision is uncertain:

1.  Prefer the simplest solution.
2.  Keep interfaces stable.
3.  Make the implementation replaceable.
4.  Add a test or diagnostic tool.
5.  Avoid large rewrites.

For example, if piece recognition using template matching is unreliable:

Do not immediately rewrite the entire project.

Instead:

``` text
PieceDetector interface
        ↓
TemplatePieceDetector
        ↓
test reliability
        ↓
if insufficient:
        ↓
MLPieceDetector
```

------------------------------------------------------------------------

# 30. Computer Vision Strategy

The CV subsystem should be treated as a pipeline.

## Stage A --- Board candidate generation

Find square regions.

## Stage B --- Board scoring

Score candidates based on chessboard characteristics.

## Stage C --- Board geometry

Determine:

``` text
x
y
width
height
square_size
```

## Stage D --- Orientation

Determine coordinate orientation.

## Stage E --- Square extraction

Produce 64 square images.

## Stage F --- Occupancy

Determine empty/occupied.

## Stage G --- Piece classification

Determine exact piece.

## Stage H --- Position validation

Check chess legality/plausibility.

## Stage I --- Temporal stability

Confirm the position across frames.

Never combine all of these into one giant function.

------------------------------------------------------------------------

# 31. Piece Recognition Strategy

Start with:

``` text
background removal
       ↓
normalisation
       ↓
template matching
       ↓
confidence
```

Templates should be stored in:

``` text
assets/piece_templates/
```

Organise them clearly.

Example:

``` text
assets/piece_templates/
├── white/
│   ├── pawn.png
│   ├── knight.png
│   ├── bishop.png
│   ├── rook.png
│   ├── queen.png
│   └── king.png
│
└── black/
    ├── pawn.png
    ├── knight.png
    ├── bishop.png
    ├── rook.png
    ├── queen.png
    └── king.png
```

Do not assume these templates will work universally.

If multiple piece sets are supported, create separate template sets.

------------------------------------------------------------------------

# 32. Improving Piece Recognition

If template matching is not sufficiently robust, try improvements in
this order:

1.  Better square cropping.
2.  Background normalisation.
3.  Scale normalisation.
4.  Multiple templates.
5.  Edge/shape features.
6.  Colour-independent features.
7.  Multiple candidate scoring.
8.  Small classifier.

Do not jump straight to a large deep-learning model.

------------------------------------------------------------------------

# 33. Board Detection Improvements

If board detection is unreliable:

1.  Improve candidate generation.
2.  Improve square-pattern scoring.
3.  Add edge/grid detection.
4.  Add colour alternation analysis.
5.  Add perspective/rectangle checks.
6.  Add temporal tracking.
7.  Use previous board location as a hint.
8.  Only then consider more advanced vision methods.

The detector should remember the last good board position and use it to
speed up tracking.

------------------------------------------------------------------------

# 34. Multi-Monitor Support

The application should eventually support multiple monitors.

At minimum:

-   enumerate monitors,
-   capture each monitor,
-   search for chessboards,
-   select highest-confidence board.

If multiple boards are detected:

-   select the highest confidence by default,
-   expose diagnostic information.

Do not assume the primary monitor is always correct.

------------------------------------------------------------------------

# 35. Window Movement and Resizing

The board may move or resize.

The application should periodically verify board geometry.

If the board is still near its previous location:

``` text
track locally
```

If it disappears:

``` text
perform full-screen detection
```

This provides better performance than scanning the whole screen
constantly.

------------------------------------------------------------------------

# 36. Overlay Behaviour

The overlay should follow the detected board.

If board geometry changes:

``` text
new geometry
    ↓
overlay.set_geometry(...)
```

The overlay must not drift away from the board.

If the board disappears:

``` text
hide overlay
```

When the board returns:

``` text
detect
 ↓
analyse
 ↓
show overlay
```

------------------------------------------------------------------------

# 37. Overlay Input Policy

The overlay must not send input to the underlying application.

The overlay's job is only:

``` text
draw information
```

The user controls the underlying application separately by hiding the
overlay.

This is an intentional architectural constraint.

------------------------------------------------------------------------

# 38. Final Acceptance Test

The project is complete only when all of the following work:

``` text
[ ] Application launches without errors.
[ ] Stockfish starts and stops correctly.
[ ] GUI is responsive.
[ ] Screen capture works.
[ ] Board is detected automatically.
[ ] Board location is detected automatically.
[ ] Board size is detected automatically.
[ ] Board orientation is detected automatically.
[ ] 64 squares are mapped correctly.
[ ] Empty squares are detected.
[ ] Pieces are detected.
[ ] Piece confidence is tracked.
[ ] Position is reconstructed.
[ ] Position is validated.
[ ] Side to move is determined where possible.
[ ] Position stability is confirmed.
[ ] FEN/position is generated.
[ ] Stockfish analyses automatically.
[ ] Best move is returned.
[ ] Multiple candidate moves are returned.
[ ] Evaluation is displayed.
[ ] Overlay aligns with board.
[ ] Best-move arrow is displayed.
[ ] Overlay follows board movement.
[ ] Overlay can be hidden with F8.
[ ] Overlay can be restored with F8.
[ ] Underlying application remains unaffected by the analyser.
[ ] Position changes trigger new analysis.
[ ] Unchanged positions do not repeatedly trigger Stockfish.
[ ] Low-confidence positions are rejected or flagged.
[ ] Errors do not crash the application.
[ ] Tests pass.
[ ] Documentation is updated.
[ ] Windows build has been tested.
[ ] macOS build has been tested.
[ ] Linux build has been tested.
[ ] Platform-specific functionality is isolated from the core application.
```

------------------------------------------------------------------------

# 39. Definition of Done

The project is not considered complete merely because the code runs.

It is complete when:

1.  The application can automatically locate a chessboard on a supported
    screen.
2.  It can identify the board orientation.
3.  It can recognise the pieces.
4.  It can reconstruct the current position.
5.  It can determine when the position is stable.
6.  It can analyse the position with Stockfish.
7.  It can display the best move and alternatives.
8.  The overlay automatically aligns with the board.
9.  The overlay can be hidden and restored.
10. The system can recover from board movement/loss.
11. The UI remains responsive.
12. The major subsystems have automated tests.
13. The application does not make moves or inject input into the
    underlying chess application.

------------------------------------------------------------------------

# 40. Recommended Implementation Sequence

Follow this exact high-level sequence:

``` text
PHASE 0
Project setup
        ↓
PHASE 1
Stockfish
        ↓
PHASE 2
Chess position model
        ↓
PHASE 3
Tkinter UI
        ↓
PHASE 4
Screen capture
        ↓
PHASE 5
Board detection
        ↓
PHASE 6
Square mapping
        ↓
PHASE 7
Orientation
        ↓
PHASE 8
Empty/occupied detection
        ↓
PHASE 9
Piece recognition
        ↓
PHASE 10
Position reconstruction
        ↓
PHASE 11
Side-to-move detection
        ↓
PHASE 12
Position stability
        ↓
PHASE 13
Automatic analysis pipeline
        ↓
PHASE 14
Transparent overlay
        ↓
PHASE 15
Move arrows
        ↓
PHASE 16
Evaluation UI
        ↓
PHASE 17
Automatic overlay alignment
        ↓
PHASE 18
Control window
        ↓
PHASE 19
Error handling
        ↓
PHASE 20
Testing
        ↓
PHASE 21
Optimisation
        ↓
PHASE 22
Packaging/release
```

Do not skip directly from Phase 1 to Phase 9.

------------------------------------------------------------------------

# 41. Final Packaging

Once development is complete, create a Windows executable.

Potential tooling:

-   PyInstaller

The packaged application should include:

-   Python dependencies,
-   application code,
-   configuration,
-   Stockfish executable,
-   required assets/templates.

Before release, test on a clean Windows machine that does not have the
development environment installed.

------------------------------------------------------------------------

# 42. Cross-Platform Release Acceptance

The project must not be considered release-ready until the major workflow has been tested on all target platforms.

Minimum release validation:

```text
[ ] Windows x86_64 build launches.
[ ] Windows x86_64 Stockfish works.
[ ] Windows screen capture works.
[ ] Windows board detection works.
[ ] Windows overlay works.

[ ] macOS build launches.
[ ] macOS Stockfish works.
[ ] macOS screen-recording permissions are handled.
[ ] macOS board detection works.
[ ] macOS overlay works.

[ ] Linux build launches.
[ ] Linux Stockfish works.
[ ] Linux screen capture works on the supported desktop/windowing environment.
[ ] Linux board detection works.
[ ] Linux overlay works where supported.

[ ] Core chess/engine/CV tests pass independently of the platform.
[ ] Platform-specific tests pass on their respective operating systems.
[ ] Packaging includes the correct platform-specific Stockfish binary.
```

A platform-specific limitation must be documented rather than hidden.

# 43. CI / Build Strategy

If continuous integration is added, prefer a build matrix with separate jobs for:

```text
Windows
macOS
Linux
```

Each job should:

1. Install the project.
2. Run unit tests.
3. Run platform-specific tests.
4. Build the application.
5. Verify that the packaged application contains the correct resources.

Do not treat a successful Windows build as proof that the macOS or Linux build works.

# 44. Final Principle

The project should be developed as a reliable engineering system rather
than a single clever script.

The critical pipeline is:

``` text
OBSERVE
  ↓
UNDERSTAND
  ↓
VALIDATE
  ↓
ANALYSE
  ↓
DISPLAY
```

The application should never blindly trust computer vision.

Every important stage should provide:

``` text
result
confidence
diagnostic information
```

The system should fail safely when uncertain and recover automatically
when the board becomes detectable again.

The final user experience should require virtually no configuration:

``` text
Launch
  ↓
Detect
  ↓
Analyse
  ↓
Display
  ↓
Track
```

The user should not need to manually describe the chessboard to the
application.
