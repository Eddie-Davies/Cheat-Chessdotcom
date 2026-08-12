@echo off
REM Chess Analyser - Build Script for Windows
REM Creates a standalone executable: dist\chess_analyser.exe

setlocal enabledelayedexpansion

echo ========================================
echo Chess Analyser - Windows Build
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found
    echo.
    echo Please run setup.bat first to create the environment
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install PyInstaller if not already installed
echo [2/3] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)
echo.

REM Build the executable
echo [3/3] Building executable...
echo This may take a few minutes...
echo.

pyinstaller chess_analyser.spec --distpath dist --buildpath build --specpath . -y

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location:
echo   dist\chess_analyser.exe
echo.
echo File size:
for %%A in (dist\chess_analyser.exe) do echo   %%~zA bytes
echo.
echo To run the application:
echo   dist\chess_analyser.exe
echo.
echo To distribute:
echo   - Copy dist\chess_analyser.exe to end users
echo   - No Python installation needed on user's system
echo.
pause
