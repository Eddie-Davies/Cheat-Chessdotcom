# Chess Analyser - Quick Start Guide

## ✅ Status: READY TO USE

Python is installed and the project is fully set up!

## One-Command Startup

```cmd
cd C:\Users\eddie\Documents\Cheat-Chessdotcom
venv\Scripts\activate.bat && python -m chess_analyser
```

## Common Commands

### Run Tests
```cmd
pytest
```
Output: **6 tests passed in 0.17s**

### Run with Coverage Report
```cmd
pytest --cov
```

### Format Code
```cmd
black src tests
```

### Check for Linting Issues
```cmd
flake8 src tests
```

### Type Checking
```cmd
mypy src
```

### View Python Info
```cmd
python --version
python -c "import sys; print(sys.executable)"
```

## Virtual Environment

### Activate (Required before running any commands)
```cmd
venv\Scripts\activate.bat
```

### Deactivate When Done
```cmd
deactivate
```

## Project Structure

```
ChessAnalyser/
├── src/chess_analyser/         ← Main application code
├── tests/                       ← Test files
├── assets/                      ← Game assets
├── engine/                      ← Stockfish binaries (Phase 1)
├── pyproject.toml               ← Project config
├── requirements.txt             ← Dependencies
└── README.md                    ← Full documentation
```

## Development Workflow

1. **Activate environment**: `venv\Scripts\activate.bat`
2. **Make changes** to code in `src/chess_analyser/`
3. **Run tests**: `pytest`
4. **Format code**: `black src tests`
5. **Check quality**: `flake8 src tests`

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/chess_analyser/main.py` | Application entry point |
| `src/chess_analyser/logging.py` | Logging configuration |
| `src/chess_analyser/config/settings.py` | Application settings |
| `tests/unit/test_*.py` | Unit tests |
| `AGENTS.md` | Development specification (READ THIS!) |

## Useful Documentation

- **AGENTS.md** - Full project specification (read first)
- **SETUP.md** - Detailed setup instructions
- **README.md** - Project overview
- **PROJECT_STRUCTURE.md** - Architecture details
- **PHASE0_SUMMARY.md** - Phase 0 completion report
- **INSTALLATION_COMPLETE.md** - Installation verification

## Troubleshooting

### "Module not found" error
- Make sure virtual environment is activated
- Check `venv\Scripts\activate.bat` ran successfully

### Tests fail to run
```cmd
pip install pytest pytest-cov
```

### Need to reinstall everything
```cmd
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -e .
```

## Next: Phase 1 - Stockfish Integration

When ready to proceed, see `AGENTS.md` section:
**"PHASE 1 --- Stockfish Integration"**

Tasks will include:
- Adding Stockfish executable
- Engine communication
- FEN analysis
- Move conversion

---

**Your system is ready!** Just run:

```cmd
venv\Scripts\activate.bat && python -m chess_analyser
```

✨ Enjoy developing Chess Analyser!
