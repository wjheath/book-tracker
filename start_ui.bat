@echo off
REM Book Tracker UI Launcher for Windows
REM This script starts the Flask server and opens the web UI

echo.
echo ============================================================
echo      ^(^) Book Tracker ^& Suggester - Web UI Launcher
echo ============================================================
echo.

REM Try multiple Python paths
set PYTHON_EXE=python
set PYTHON_FOUND=0

REM Try: C:\Program Files\Python310\python.exe (common location)
if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python310\python.exe
    set PYTHON_FOUND=1
    goto :python_found
)

REM Try: C:\Program Files\Python311\python.exe
if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python311\python.exe
    set PYTHON_FOUND=1
    goto :python_found
)

REM Try: C:\Program Files\Python39\python.exe
if exist "C:\Program Files\Python39\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python39\python.exe
    set PYTHON_FOUND=1
    goto :python_found
)

REM Try: default python in PATH
python --version >nul 2>&1
if errorlevel 0 (
    set PYTHON_FOUND=1
    goto :python_found
)

REM Python not found
echo ERROR: Python is not installed or not in PATH
echo.
echo Please install Python 3.8+ from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:python_found
echo Using Python: %PYTHON_EXE%
echo.

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create a .env file with your OpenAI API key.
    echo See .env.example for a template.
    echo.
)

REM Start the Flask app
echo Starting Flask API server...
echo.

%PYTHON_EXE% run_ui.py

pause
