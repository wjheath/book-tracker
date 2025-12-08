@echo off
REM Book Tracker Web UI Launcher
REM This script starts the Flask app and opens the browser

echo ============================================================
echo   Book Tracker Web UI Launcher
echo ============================================================
echo.

REM Try to find Python in common locations
set PYTHON_EXE=

REM Check Program Files
if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_EXE="C:\Program Files\Python310\python.exe"
    echo ^✓ Found Python at: C:\Program Files\Python310
    goto start_app
)

if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE="C:\Program Files\Python311\python.exe"
    echo ^✓ Found Python at: C:\Program Files\Python311
    goto start_app
)

if exist "C:\Program Files\Python312\python.exe" (
    set PYTHON_EXE="C:\Program Files\Python312\python.exe"
    echo ^✓ Found Python at: C:\Program Files\Python312
    goto start_app
)

REM Try using where command
for /f "delims=" %%i in ('where python 2^>nul') do (
    set PYTHON_EXE="%%i"
    echo ^✓ Found Python in PATH: %%i
    goto start_app
)

REM If we get here, Python not found
echo.
echo ERROR: Python not found!
echo.
echo Please:
echo  1. Install Python from https://www.python.org/downloads/
echo  2. Make sure to check "Add Python to PATH" during install
echo  3. Restart your computer
echo  4. Try again
echo.
pause
exit /b 1

:start_app
echo.
echo Installing/verifying dependencies...
%PYTHON_EXE% -m pip install -q -r requirements.txt 2>nul
if errorlevel 1 (
    echo WARNING: Could not verify packages
)
echo.
echo ============================================================
echo   Starting Flask App on http://127.0.0.1:5000
echo ============================================================
echo.
echo Waiting for server to start ^(5 seconds^)...
timeout /t 5 /nobreak

echo.
echo Opening browser...
start http://127.0.0.1:5000

echo.
echo Running Flask server... Press CTRL+C to stop
echo.
%PYTHON_EXE% src\app.py
pause
exit /b 0
