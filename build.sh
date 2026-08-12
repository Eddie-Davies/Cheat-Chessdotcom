#!/bin/bash
# Chess Analyser - Build Script for macOS and Linux
# Creates standalone executable: dist/chess_analyser

set -e

echo "========================================"
echo "Chess Analyser - $(uname -s) Build"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found"
    echo ""
    echo "Please run setup.sh first to create the environment"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source venv/bin/activate
echo ""

# Install PyInstaller if not already installed
echo "[2/3] Checking PyInstaller..."
pip show pyinstaller >/dev/null 2>&1 || {
    echo "Installing PyInstaller..."
    pip install pyinstaller
}
echo ""

# Build the executable
echo "[3/3] Building executable..."
echo "This may take a few minutes..."
echo ""

pyinstaller chess_analyser.spec --distpath dist --buildpath build --specpath . -y

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""

# Determine executable name based on OS
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    echo "Application bundle location:"
    echo "  dist/chess_analyser.app"
    echo ""
    echo "File size:"
    du -sh "dist/chess_analyser.app"
    echo ""
    echo "To run the application:"
    echo "  open dist/chess_analyser.app"
    echo ""
    echo "To distribute:"
    echo "  - Create a .dmg file"
    echo "  - Users can drag chess_analyser.app to /Applications"
    echo ""
elif [ "$(uname)" == "Linux" ]; then
    # Linux
    echo "Executable location:"
    echo "  dist/chess_analyser/chess_analyser"
    echo ""
    echo "File size:"
    du -sh "dist/chess_analyser"
    echo ""
    echo "To run the application:"
    echo "  ./dist/chess_analyser/chess_analyser"
    echo ""
    echo "To distribute:"
    echo "  - Create an AppImage: python -m pip install appimagetool"
    echo "  - Or package as .deb/.rpm"
    echo "  - Or compress dist/chess_analyser as .tar.gz"
    echo ""
fi

echo "No Python installation needed on user's system!"
