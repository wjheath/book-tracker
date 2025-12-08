#!/usr/bin/env powershell
# Book Tracker Web UI Launcher
# Starts Flask app and opens browser

Write-Host "============================================================"
Write-Host "  Book Tracker Web UI Launcher"
Write-Host "============================================================"
Write-Host ""

# Find Python
$PythonExe = $null

# Check common locations
$PythonPaths = @(
    "C:\Program Files\Python310\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python39\python.exe"
)

foreach ($path in $PythonPaths) {
    if (Test-Path $path) {
        $PythonExe = $path
        Write-Host "✓ Found Python at: $path"
        break
    }
}

# Try where command
if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($PythonExe) {
        Write-Host "✓ Found Python in PATH: $PythonExe"
    }
}

# Error if not found
if (-not $PythonExe) {
    Write-Host ""
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from https://www.python.org/downloads/"
    Write-Host "Make sure to check 'Add Python to PATH' during install"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing/verifying dependencies..."
& $PythonExe -m pip install -q -r requirements.txt 2>$null

Write-Host ""
Write-Host "============================================================"
Write-Host "  Starting Flask App on http://127.0.0.1:5000"
Write-Host "============================================================"
Write-Host ""
Write-Host "Waiting 3 seconds for server to start..."
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Opening browser to http://127.0.0.1:5000..."
Start-Process "http://127.0.0.1:5000"

Write-Host ""
Write-Host "Running Flask server... Press CTRL+C to stop"
Write-Host ""
& $PythonExe src\app.py
