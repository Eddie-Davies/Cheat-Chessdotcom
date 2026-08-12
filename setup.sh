#!/bin/bash
# Chess Analyser Setup Script for macOS and Linux
# This script sets up the project environment and runs tests

set -e  # Exit on error

echo "========================================"
echo "Chess Analyser - Environment Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Please install Python 3.12+ using one of these methods:"
    echo "  macOS (Homebrew): brew install python@3.12"
    echo "  Ubuntu/Debian: sudo apt-get install python3.12"
    echo "  Fedora: sudo dnf install python3.12"
    echo "  Or download from: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo "[1/5] Python is installed:"
python3 --version
echo ""

# Check if Git is installed (optional but recommended)
if command -v git &> /dev/null; then
    echo "[2/5] Git is installed:"
    git --version
else
    echo "[2/5] WARNING: Git is not installed. Recommended for version control."
fi
echo ""

# Create virtual environment
echo "[3/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    echo "Virtual environment created successfully"
fi
echo ""

# Activate virtual environment
echo "[4/5] Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated"
echo ""

# Upgrade pip
echo "[4.5/5] Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo ""

# Install dependencies
echo "[5/5] Installing dependencies..."
pip install -r requirements.txt
echo "Dependencies installed successfully"
echo ""

# Verify installation
echo "========================================"
echo "Verifying Installation"
echo "========================================"
echo ""

echo "Testing Python import..."
python -c "import chess_analyser; print('✓ chess_analyser package imports successfully')"
echo ""

echo "Testing application startup..."
python -m chess_analyser
echo ""

# Run tests
echo "========================================"
echo "Running Tests"
echo "========================================"
echo ""

pytest tests/ -v || {
    echo ""
    echo "WARNING: Some tests failed"
    echo ""
}

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Your Chess Analyser development environment is ready."
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To run the application:"
echo "  python -m chess_analyser"
echo ""
echo "Next: Read AGENTS.md for development guidelines"
echo ""
