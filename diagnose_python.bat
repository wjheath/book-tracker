@echo off
REM Debug script to help diagnose Python issues
REM Run this if you're having problems

echo.
echo ========================================
echo BOOK TRACKER - PYTHON DIAGNOSTIC
echo ========================================
echo.

echo [1] Checking for Python in PATH...
where python >nul 2>&1
if errorlevel 1 (
    echo    RESULT: NOT FOUND
) else (
    echo    RESULT: FOUND
    for /f "tokens=*" %%i in ('where python') do echo    Path: %%i
)

echo.
echo [2] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo    RESULT: Cannot run python --version
) else (
    python --version
)

echo.
echo [3] Checking common installation paths...

if exist "C:\Program Files\Python310\python.exe" (
    echo    FOUND: C:\Program Files\Python310\python.exe
) else (
    echo    NOT FOUND: C:\Program Files\Python310\
)

if exist "C:\Program Files\Python311\python.exe" (
    echo    FOUND: C:\Program Files\Python311\python.exe
) else (
    echo    NOT FOUND: C:\Program Files\Python311\
)

if exist "C:\Program Files\Python39\python.exe" (
    echo    FOUND: C:\Program Files\Python39\python.exe
) else (
    echo    NOT FOUND: C:\Program Files\Python39\
)

if exist "C:\Program Files\Python38\python.exe" (
    echo    FOUND: C:\Program Files\Python38\python.exe
) else (
    echo    NOT FOUND: C:\Program Files\Python38\
)

echo.
echo [4] Checking for Flask...
python -c "import flask; print('Flask version:', flask.__version__)" >nul 2>&1
if errorlevel 1 (
    echo    RESULT: Flask NOT installed
) else (
    for /f "tokens=*" %%i in ('python -c "import flask; print('Flask version:', flask.__version__)"') do echo    RESULT: %%i
)

echo.
echo [5] Checking for book database...
if exist "data\books.db" (
    echo    RESULT: FOUND books.db
) else (
    echo    RESULT: NOT FOUND books.db
)

echo.
echo ========================================
echo RECOMMENDATIONS:
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo - Python is NOT in your PATH
    echo - Try using: start_ui_simple.bat
    echo - Or install Python with "Add Python to PATH" checked
) else (
    echo - Python IS in your PATH
    echo - Try: python run_ui.py
)

echo.
echo ========================================
echo.
pause
