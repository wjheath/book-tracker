@echo off
REM Simple finder - just starts the Flask app with whatever Python we can find

setlocal enabledelayedexpansion

echo.
echo Finding Python...
echo.

REM Try to find Python using where command
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set PYTHON_PATH=%%i
    goto :found
)

REM Try common installation paths
if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python310\python.exe
    goto :found
)

if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python311\python.exe
    goto :found
)

if exist "C:\Program Files\Python39\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python39\python.exe
    goto :found
)

if exist "C:\Program Files\Python38\python.exe" (
    set PYTHON_PATH=C:\Program Files\Python38\python.exe
    goto :found
)

REM Python not found
echo ERROR: Cannot find Python!
echo.
echo Please install Python 3.8+ from https://www.python.org/
echo Check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found
echo Found Python: !PYTHON_PATH!
echo.
echo Starting Book Tracker UI...
echo.

"!PYTHON_PATH!" run_ui.py

pause
