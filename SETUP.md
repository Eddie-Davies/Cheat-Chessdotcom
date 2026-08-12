# Chess Analyser - Setup Guide

## Phase 0: Repository Setup - COMPLETE ✓

The complete project structure has been created. This document explains how to set up the environment and verify the installation.

## System Requirements

- Python 3.12+ (must be installed from python.org or another package manager, not Microsoft Store shortcut)
- Git
- VS Code (optional but recommended)

## Step 1: Install Python

### Option A: Direct Installation from python.org (Recommended)

1. Download Python 3.12+ from https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```powershell
   python --version
   ```

### Option B: Using Chocolatey (Windows)

```powershell
choco install python --version=3.12.0
```

### Option C: Using Miniconda

1. Download Miniconda from https://docs.conda.io/projects/miniconda/en/latest/
2. Run the installer
3. Verify installation:
   ```powershell
   conda --version
   ```

## Step 2: Set Up Virtual Environment

Navigate to the project directory:

```powershell
cd c:\Users\eddie\Documents\Cheat-Chessdotcom
```

### Create Virtual Environment

```powershell
python -m venv venv
```

### Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt after activation.

## Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

Or for development (includes testing tools):

```powershell
pip install -e ".[dev]"
```

## Step 4: Verify Installation

### Import the package:
```powershell
python -c "import chess_analyser; print('✓ Package imports successfully')"
```

### Run the application:
```powershell
python -m chess_analyser
```

Expected output:
```
✓ Chess Analyser initialized successfully
✓ Phase 0 (Repository Setup) complete
```

### Run tests:
```powershell
pytest
```

Expected output:
```
tests/unit/test_initialization.py::test_version PASSED
tests/unit/test_initialization.py::test_default_settings PASSED
tests/unit/test_initialization.py::test_settings_validation PASSED
tests/unit/test_initialization.py::test_logging_setup PASSED
tests/unit/test_initialization.py::test_get_logger PASSED
tests/unit/test_main.py::test_main_runs_without_error PASSED

====== 6 passed in X.XXs ======
```

## Step 5: Configure VS Code (Optional)

1. Open the workspace folder in VS Code
2. Install the Python extension (ms-python.python)
3. Select the Python interpreter:
   - Press Ctrl+Shift+P
   - Type "Python: Select Interpreter"
   - Choose the one from `./venv/bin/python` or `./venv/Scripts/python.exe`

## Project Structure

```
ChessAnalyser/
├── AGENTS.md              # Development guide (mandatory reading)
├── README.md              # Project overview
├── SETUP.md               # This file
├── pyproject.toml         # Project metadata and configuration
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
│
├── src/chess_analyser/    # Main application package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point for python -m chess_analyser
│   ├── main.py            # Main application logic
│   ├── logging.py         # Logging configuration
│   │
│   ├── config/            # Configuration module
│   │   ├── __init__.py
│   │   └── settings.py    # Application settings
│   │
│   ├── capture/           # Screen capture (Phase 4)
│   ├── detection/         # Board/piece detection (Phases 5-9)
│   ├── chess/             # Position management (Phase 2)
│   ├── engine/            # Stockfish integration (Phase 1)
│   ├── overlay/           # Visual overlay (Phase 14-17)
│   ├── ui/                # User interface (Phase 3)
│   └── pipeline/          # Analysis pipeline (Phase 13)
│
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest configuration
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data and fixtures
│
├── assets/                # Application assets
│   ├── piece_templates/   # Piece recognition templates (Phase 9)
│   └── test_screens/      # Test screenshots (Phase 5+)
│
└── engine/                # Stockfish executables
    └── stockfish/
        ├── windows/       # Windows binary
        ├── macos/         # macOS binary
        └── linux/         # Linux binary
```

## Next Steps

Once the environment is set up, the next phase is:

**Phase 1: Stockfish Integration**
- Add Stockfish executable
- Implement engine startup/shutdown
- Add FEN analysis capability
- Add engine tests

## Troubleshooting

### "python: command not found"

Make sure Python is installed and added to PATH. Reinstall from python.org if needed.

### Module not found errors

Make sure the virtual environment is activated:
```powershell
.\venv\Scripts\Activate.ps1  # On Windows PowerShell
```

### Pytest not found

Install development dependencies:
```powershell
pip install -r requirements.txt
pip install pytest
```

### Permission errors on macOS/Linux

Use `chmod` if needed:
```bash
chmod +x venv/bin/activate
```

## Cross-Platform Notes

This project is designed to work on:
- ✓ Windows (PowerShell, CMD)
- ✓ macOS (Terminal, zsh, bash)
- ✓ Linux (bash, zsh, etc.)

All code avoids Windows-only APIs and uses cross-platform libraries like:
- `mss` for screen capture
- `opencv-python` for computer vision
- `tkinter` for UI (built-in)
- `python-chess` for chess logic

## Development Workflow

1. Activate virtual environment
2. Make changes
3. Run tests: `pytest`
4. Format code: `black src tests`
5. Lint code: `flake8 src tests`
6. Type check: `mypy src`

## Getting Help

See AGENTS.md for the complete project specification and development guidelines.
