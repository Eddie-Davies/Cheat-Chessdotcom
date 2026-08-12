@echo off
REM Chess Analyser Setup Script for Windows
REM This script sets up the project environment and runs tests
REM Uses Python 3.14 from AppData\Local\Programs\Python\Python314

setlocal enabledelayedexpansion

set PYTHON_PATH=C:\Users\eddie\AppData\Local\Programs\Python\Python314\python.exe

echo ========================================
echo Chess Analyser - Environment Setup
echo ========================================
echo.

REM Check if Python is installed
if not exist "!PYTHON_PATH!" (
    echo ERROR: Python not found at !PYTHON_PATH!
    echo.
    echo Please check your Python installation.
    echo.
    pause
    exit /b 1
)

echo [1/5] Python is installed:
"!PYTHON_PATH!" --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping creation
) else (
    "!PYTHON_PATH!" -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Upgrade pip and install dependencies
echo [4/5] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Verify installation
echo ========================================
echo Verifying Installation
echo ========================================
echo.

echo Testing Python import...
python -c "import chess_analyser; print('✓ chess_analyser package imports successfully')"
if errorlevel 1 (
    echo ERROR: Failed to import chess_analyser
    pause
    exit /b 1
)
echo.

echo Testing application startup...
python -m chess_analyser
if errorlevel 1 (
    echo WARNING: Application did not start cleanly
)
echo.

echo ========================================
echo Running Tests
echo ========================================
echo.

pytest tests/ -v
if errorlevel 1 (
    echo WARNING: Some tests failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Your Chess Analyser development environment is ready.
echo.
echo To activate the environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To run tests:
echo   pytest
echo.
echo To run the application:
echo   python -m chess_analyser
echo.
echo Next: Read AGENTS.md for development guidelines
echo.
pause
