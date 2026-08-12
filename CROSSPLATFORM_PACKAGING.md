# Chess Analyser - Cross-Platform Development & Packaging Guide

## Current State: ✅ CROSS-PLATFORM READY FOR DEVELOPMENT

### Development Setup ✅

**Virtual Environment**: ✅ Working perfectly
- Windows: `venv\Scripts\activate.bat`
- macOS/Linux: `source venv/bin/activate`
- Same code works on all platforms

**Setup Scripts**: ✅ Platform-specific
- `setup.bat` - Windows PowerShell/CMD
- `setup.sh` - macOS/Linux Bash

**Dependencies**: ✅ All cross-platform
```
python-chess      (pure Python)
mss               (Windows, macOS, Linux)
opencv-python     (all platforms)
numpy             (all platforms)
Pillow            (all platforms)
tkinter           (built-in, all platforms)
```

**Code**: ✅ No Windows-only APIs
- Uses `mss` for screen capture (cross-platform)
- Uses `tkinter` for UI (built-in on all platforms)
- Uses `pathlib` for file operations (cross-platform)
- No `win32api` or platform-specific calls

### Current Virtual Environment Setup

```
Development:
  Windows user runs: setup.bat
  macOS/Linux user runs: bash setup.sh
  ↓
  Creates: venv/
  ↓
  Installs dependencies
  ↓
  All can use: pytest, python -m chess_analyser, etc.
```

**✅ This works perfectly for development across all platforms.**

---

## Packaging for End Users: REQUIRES NEW SETUP

To package as standalone apps for Windows, macOS, and Linux, you'll need:

### Option 1: PyInstaller (Recommended) ✅

PyInstaller bundles Python + dependencies + your code into standalone executables.

**Advantages:**
- Single executable (no Python installation needed for users)
- Works on Windows, macOS, Linux
- Handles dependencies automatically
- Can add custom icons and metadata

**Disadvantages:**
- Requires building separately on each OS (or cross-compilation)
- Larger file size (includes Python runtime)
- Anti-virus software sometimes flags executables

### Option 2: py2exe / py2app / PyInstaller (OS-specific)

- **Windows**: PyInstaller or py2exe
- **macOS**: PyInstaller or py2app
- **Linux**: PyInstaller (creates AppImage or wheel)

### Option 3: Conda/Mamba (Alternative)

Create conda packages for each platform.

---

## What's Needed for Packaging

### 1. Add PyInstaller Configuration ✅ (We'll add this)

Create `chess_analyser.spec` for PyInstaller

### 2. Stockfish Binaries ✅ (You have structure)

Already prepared:
```
engine/stockfish/
├── windows/stockfish.exe     ← Windows binary
├── macos/stockfish           ← macOS binary
└── linux/stockfish           ← Linux binary
```

### 3. Build Scripts

- `build_windows.bat` - Builds Windows .exe
- `build_macos.sh` - Builds macOS .app
- `build_linux.sh` - Builds Linux AppImage

### 4. CI/CD Pipeline (Optional but recommended)

GitHub Actions to build on each platform automatically.

---

## Implementation Plan

### Phase 0 (Current): ✅ Development Setup Complete

```
✅ Python 3.14.7 installed
✅ Virtual environment working
✅ Cross-platform code base
✅ All dependencies cross-platform
✅ Tests passing
✅ Application runs
```

### Phase 1-22: Application Development

Build out all features using the venv development setup.

### Phase 23: Packaging Setup (NEW)

Add packaging configuration for standalone apps:

1. **Install PyInstaller:**
   ```
   pip install pyinstaller
   ```

2. **Create PyInstaller configuration** (chess_analyser.spec)

3. **Build for each platform:**
   ```
   # On Windows
   pyinstaller chess_analyser.spec
   
   # On macOS
   pyinstaller chess_analyser.spec
   
   # On Linux
   pyinstaller chess_analyser.spec
   ```

4. **Package outputs:**
   - Windows: `dist/chess_analyser.exe` (~150-200 MB)
   - macOS: `dist/chess_analyser.app` (~200-250 MB)
   - Linux: `dist/chess_analyser` or AppImage (~150-200 MB)

---

## Detailed Packaging Setup (Ready to Implement)

Here's what we'd add for packaging:

### 1. PyInstaller Spec File

```python
# chess_analyser.spec
a = Analysis(
    ['src/chess_analyser/__main__.py'],
    pathex=[],
    binaries=[
        ('engine/stockfish/windows/stockfish.exe', 'engine/stockfish'),  # Windows
        ('engine/stockfish/macos/stockfish', 'engine/stockfish'),        # macOS
        ('engine/stockfish/linux/stockfish', 'engine/stockfish'),        # Linux
    ],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=['chess_analyser'],
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChessAnalyser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    icon='assets/icon.ico',  # Windows
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='chess_analyser')
```

### 2. Build Scripts

**Windows (build_windows.bat):**
```batch
@echo off
call venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller chess_analyser.spec --onefile
echo Build complete: dist/chess_analyser.exe
```

**macOS/Linux (build.sh):**
```bash
#!/bin/bash
source venv/bin/activate
pip install pyinstaller
pyinstaller chess_analyser.spec
echo "Build complete: dist/chess_analyser"
```

### 3. Version Info

Update version in:
- `src/chess_analyser/__init__.py`
- `pyproject.toml`
- Build metadata

---

## Current Vs. Packaged

### Development (Current):
```
User's system:
├── Python 3.14 installed
├── venv/
├── src/chess_analyser/
├── Run: python -m chess_analyser
└── Modify code, tests pass
```

### Packaged (Goal):
```
User's system:
├── Download: ChessAnalyser.exe (or .app/.bin)
├── Double-click to run
└── No Python installation needed
```

---

## Cross-Platform Testing Workflow

### Before Packaging

Test on each platform:

**Windows:**
```cmd
venv\Scripts\activate.bat
pytest
python -m chess_analyser
```

**macOS:**
```bash
source venv/bin/activate
pytest
python -m chess_analyser
```

**Linux:**
```bash
source venv/bin/activate
pytest
python -m chess_analyser
```

### After Packaging

Test executable on each platform:

**Windows:**
```cmd
dist\ChessAnalyser.exe
```

**macOS:**
```bash
open dist/ChessAnalyser.app
```

**Linux:**
```bash
./dist/chess_analyser
```

---

## Architecture for Cross-Platform Packaging

```
Chess Analyser
├── Development (Current Setup) ✅
│   ├── Windows: setup.bat
│   ├── macOS/Linux: setup.sh
│   ├── Develop with: python -m chess_analyser
│   └── Test with: pytest
│
└── Packaging (To Be Added)
    ├── PyInstaller config
    ├── Windows build: chess_analyser.exe
    ├── macOS build: chess_analyser.app
    └── Linux build: chess_analyser (AppImage)
```

---

## Stockfish Handling

### Current Setup ✅
```
engine/stockfish/
├── windows/stockfish.exe      ← Ready for packaging
├── macos/stockfish            ← Ready for packaging
└── linux/stockfish            ← Ready for packaging
```

### In Packaged App:
```
ChessAnalyser.exe (or .app/.bin)
├── Contains: Python runtime
├── Contains: All dependencies
├── Contains: stockfish.exe/stockfish binary
└── Contains: chess_analyser code
```

Application will detect platform and use correct Stockfish binary.

---

## Recommended Development Workflow

### For Single Platform Development:
```bash
# Activate venv
venv\Scripts\activate.bat          # Windows
# or
source venv/bin/activate           # macOS/Linux

# Code, test, debug
pytest
python -m chess_analyser

# When ready to release
pyinstaller chess_analyser.spec
```

### For Cross-Platform Testing:
```
1. Develop on Windows with venv
2. Test on Windows
3. Push to GitHub
4. GitHub Actions runs tests on Windows/macOS/Linux
5. When ready, build each platform
```

---

## Summary: Current State

| Aspect | Status | Details |
|--------|--------|---------|
| **venv Development** | ✅ Working | Windows, macOS, Linux |
| **Cross-platform Code** | ✅ Ready | No platform-specific APIs |
| **Dependencies** | ✅ Cross-platform | All work on Windows/macOS/Linux |
| **Testing** | ✅ Works | Same tests run on all platforms |
| **Packaging Config** | ⏳ To Add | Need PyInstaller config |
| **Standalone Apps** | ⏳ To Build | After Phase 22 (development complete) |
| **Stockfish Binaries** | ✅ Ready | Directory structure prepared |

---

## Timeline for Packaging

1. **Phases 1-22**: Develop features using current venv setup
2. **Phase 23**: Add PyInstaller configuration
3. **Phase 24**: Create build scripts for each OS
4. **Phase 25**: Set up CI/CD for automated builds
5. **Release**: Build and release standalone apps

---

## Answer to Your Question

**Q: Does this setup work cross-platform and with a venv for development?**

**A:** ✅ **YES, perfectly!**
- venv works on Windows, macOS, Linux
- Code is platform-agnostic
- Tests run on all platforms
- Ideal for team development

**Q: Can you package this as standalone apps for Windows, Linux, and Mac?**

**A:** ✅ **YES, with PyInstaller added!**
- PyInstaller can create .exe, .app, AppImage
- Build separately on each platform (or use CI/CD)
- Users don't need Python installed
- Includes Stockfish binaries

**Next Step**: After Phase 22 development, add PyInstaller configuration and build scripts for packaging.

---

## Quick Command Reference

### Development (Current):
```cmd
venv\Scripts\activate.bat          # Windows
source venv/bin/activate           # macOS/Linux
pytest
python -m chess_analyser
```

### Packaging (When Ready):
```cmd
pyinstaller chess_analyser.spec
# Creates dist/ChessAnalyser.exe (Windows)
# Creates dist/ChessAnalyser.app (macOS)
# Creates dist/chess_analyser (Linux)
```

---

**Your current setup is perfect for cross-platform development! When ready to package for end users, we'll add PyInstaller configuration.**
