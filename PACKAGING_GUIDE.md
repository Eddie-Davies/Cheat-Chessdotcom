# Chess Analyser - Packaging & Distribution Guide

## Overview

After developing Chess Analyser through Phase 22, use these tools to create standalone applications for Windows, macOS, and Linux users.

## What You're Creating

**Before**: Users need Python 3.14+ installed + all dependencies
```
User's computer:
├── Python 3.14
├── pip install -r requirements.txt
├── python -m chess_analyser
```

**After**: Users just run the app
```
User's computer:
├── Download: ChessAnalyser.exe / ChessAnalyser.app / chess_analyser
├── Double-click
└── App launches (no Python needed)
```

## Files Provided

### 1. `chess_analyser.spec`
- **What**: PyInstaller configuration
- **Why**: Defines how to bundle Python + dependencies into executable
- **Cross-platform**: Detects OS and includes correct Stockfish binary

### 2. `build_windows.bat`
- **What**: Windows build script
- **Output**: `dist\chess_analyser.exe` (~150-200 MB)
- **Usage**: Double-click or run from PowerShell

### 3. `build.sh`
- **What**: macOS/Linux build script
- **Output**: `dist/chess_analyser.app` (macOS) or `dist/chess_analyser/` (Linux)
- **Usage**: `bash build.sh`

---

## Prerequisites Before Building

### All Platforms

1. **Have built and tested the application through Phase 22**
   ```cmd
   python -m chess_analyser          # Should work
   pytest                             # All tests pass
   ```

2. **Install PyInstaller**
   ```cmd
   pip install pyinstaller
   ```

3. **Stockfish Binaries Ready**
   - Ensure these files exist with execute permissions:
     ```
     engine/stockfish/windows/stockfish.exe
     engine/stockfish/macos/stockfish
     engine/stockfish/linux/stockfish
     ```

### Platform-Specific

**Windows**: Nothing extra needed

**macOS**:
```bash
# Make Stockfish executable
chmod +x engine/stockfish/macos/stockfish
```

**Linux**:
```bash
# Make Stockfish executable
chmod +x engine/stockfish/linux/stockfish
```

---

## Building on Each Platform

### Windows Build

**Option 1: Simple (GUI)**
```
1. Open File Explorer
2. Navigate to: C:\Users\eddie\Documents\Cheat-Chessdotcom
3. Double-click: build_windows.bat
4. Wait 5-10 minutes
5. Result: dist\chess_analyser.exe
```

**Option 2: Command Line**
```cmd
cd C:\Users\eddie\Documents\Cheat-Chessdotcom
venv\Scripts\activate.bat
pyinstaller chess_analyser.spec
```

**Output:**
```
dist/
└── chess_analyser.exe          (175 MB, includes Python + all dependencies)
```

### macOS Build

```bash
cd /path/to/Chess-Analyser
bash build.sh
```

**Output:**
```
dist/
└── chess_analyser.app/
    ├── Contents/
    │   ├── MacOS/chess_analyser
    │   ├── Resources/
    │   └── Info.plist
    └── (250+ MB)
```

### Linux Build

```bash
cd /path/to/Chess-Analyser
bash build.sh
```

**Output:**
```
dist/
└── chess_analyser/
    ├── chess_analyser        (executable)
    ├── engine/
    └── ... (dependencies)
```

---

## Building on Different Machine

**Problem**: You only have Windows, but need to build for macOS and Linux

**Solution**: Use CI/CD (GitHub Actions) to build automatically

### Setup CI/CD (GitHub Actions)

Create `.github/workflows/build.yml`:

```yaml
name: Build Chess Analyser

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: |
          pip install -r requirements.txt
          pip install pyinstaller
          pyinstaller chess_analyser.spec
      - uses: actions/upload-artifact@v2
        with:
          name: chess_analyser-windows
          path: dist/chess_analyser.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: |
          pip install -r requirements.txt
          pip install pyinstaller
          pyinstaller chess_analyser.spec
      - uses: actions/upload-artifact@v2
        with:
          name: chess_analyser-macos
          path: dist/chess_analyser.app

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: |
          pip install -r requirements.txt
          pip install pyinstaller
          pyinstaller chess_analyser.spec
      - uses: actions/upload-artifact@v2
        with:
          name: chess_analyser-linux
          path: dist/chess_analyser
```

Then:
1. Push code to GitHub
2. Create a git tag: `git tag v0.1.0`
3. Push tag: `git push origin v0.1.0`
4. GitHub Actions automatically builds all three versions
5. Download built binaries from GitHub Actions artifacts

---

## Distribution

### Windows Users

```
chess_analyser.exe
└── Can be:
    ├── Distributed directly
    ├── Packaged in installer (NSIS)
    ├── Uploaded to Windows Store
    └── Posted on SourceForge/GitHub Releases
```

**Optional: Create Installer**
```
Install NSIS: https://nsis.sourceforge.io/
Create: installer.nsi
Run: makensis installer.nsi
Result: ChessAnalyser-Setup.exe
```

### macOS Users

```
chess_analyser.app
└── Can be:
    ├── Distributed directly
    ├── Packaged in .dmg file
    └── Signed and notarized (for App Store)
```

**Create .dmg file:**
```bash
brew install create-dmg
create-dmg dist/chess_analyser.app
# Creates: chess_analyser.dmg
```

### Linux Users

```
chess_analyser (executable folder)
└── Can be:
    ├── Distributed as .tar.gz
    ├── Created as AppImage
    ├── Packaged as .deb (Debian/Ubuntu)
    ├── Packaged as .rpm (Red Hat/Fedora)
    └── Uploaded to Snap Store
```

**Create AppImage:**
```bash
pip install appimagetool
appimagetool dist/chess_analyser chess_analyser.AppImage
chmod +x chess_analyser.AppImage
```

**Create .tar.gz:**
```bash
tar czf chess_analyser.tar.gz dist/chess_analyser/
```

---

## Testing Packaged App

### Windows
```cmd
# Run the .exe
dist\chess_analyser.exe
```

### macOS
```bash
# Run the app bundle
open dist/chess_analyser.app

# Or direct
./dist/chess_analyser.app/Contents/MacOS/chess_analyser
```

### Linux
```bash
# Run the executable
./dist/chess_analyser/chess_analyser
```

---

## Troubleshooting

### "Stockfish not found"

**Windows:**
```
ERROR: engine/stockfish/windows/stockfish.exe not found
```

**Fix:** Download Stockfish executable and place in:
```
engine/stockfish/windows/stockfish.exe
```

**macOS/Linux:**
```bash
# Make sure file is executable
chmod +x engine/stockfish/macos/stockfish
chmod +x engine/stockfish/linux/stockfish
```

### PyInstaller Not Found

```
ERROR: 'pyinstaller' is not recognized
```

**Fix:**
```cmd
pip install pyinstaller
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'xyz'
```

**Fix:**
1. Ensure all packages are in `requirements.txt`
2. Add to `chess_analyser.spec` in `hiddenimports`
3. Rebuild

### File Too Large

PyInstaller bundles everything, resulting in large file sizes:
- Windows .exe: 150-200 MB
- macOS .app: 200-250 MB
- Linux: 150-200 MB

To reduce:
1. Use UPX compression (included)
2. Remove unused dependencies
3. Remove debug symbols

---

## Version Management

Update before each build:

```python
# src/chess_analyser/__init__.py
__version__ = "0.2.0"
```

```toml
# pyproject.toml
version = "0.2.0"
```

Also update in build output filenames:
- Windows: `chess_analyser_v0.2.0.exe`
- macOS: `chess_analyser_v0.2.0.dmg`
- Linux: `chess_analyser_v0.2.0.tar.gz`

---

## Release Checklist

- [ ] All tests pass: `pytest`
- [ ] Application works: `python -m chess_analyser`
- [ ] Version bumped in `__init__.py` and `pyproject.toml`
- [ ] Build script runs without errors
- [ ] Packaged app runs without Python installed
- [ ] All dependencies included (test on clean machine)
- [ ] Stockfish binary works in packaged app
- [ ] Create GitHub Release with binaries
- [ ] Update version in documentation

---

## Build Times

- **Windows**: 5-10 minutes (includes Python + all deps)
- **macOS**: 5-10 minutes
- **Linux**: 5-10 minutes

Times vary based on:
- System speed
- Number of dependencies
- Stockfish binary size

---

## Summary

### For Development (Current):
```
venv\Scripts\activate.bat
python -m chess_analyser
```

### For Users:
```
Double-click: chess_analyser.exe / .app / binary
```

### Build Process:
```
Windows: build_windows.bat
macOS/Linux: bash build.sh
```

### Full Distribution Workflow:
1. Develop and test (Phases 1-22) ✅ Done
2. Run build script
3. Test packaged app
4. Upload to distribution platform
5. Users download and run (no Python needed)

---

## Next Steps When Ready

1. **Ensure Stockfish binaries are available** in `engine/stockfish/`
2. **Complete Phase 22** of development
3. **Run**: `build_windows.bat` or `bash build.sh`
4. **Test**: Run `dist/chess_analyser.exe` (or equivalent)
5. **Distribute**: Share with users

**You're ready to package Chess Analyser for end users!** 🎉
