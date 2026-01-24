@echo off
REM Book Tracker App Launcher for Windows

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ========================================
echo   Book Tracker ^& Suggester
echo ========================================
echo.

REM Check for virtual environment in parent folder first (common setup), then local
if exist "..\.venv\Scripts\python.exe" (
    echo Using parent virtual environment...
    "..\.venv\Scripts\python.exe" run_ui.py
    goto :end
)

if exist ".venv\Scripts\python.exe" (
    echo Using local virtual environment...
    ".venv\Scripts\python.exe" run_ui.py
    goto :end
)

REM Try Python from PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting app...
    python run_ui.py
    goto :end
)

REM Try py launcher (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting app...
    py run_ui.py
    goto :end
)

REM Python not found
echo ERROR: Python not found!
echo.
echo Please install Python 3.8+ from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
echo.

:end
pause
