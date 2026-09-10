@echo off
setlocal
cd /d %~dp0

echo ====================================================
echo   Mark Motors Group - Invoice Approval Launcher
echo ====================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo [1/3] Creating virtual environment... This may take a minute...
    python -m venv venv
)

:: Check if requirements need to be installed
echo [2/3] Checking/Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt --quiet

:: Run the application
echo [3/3] Starting Invoice Approval...
python invoice_stamper.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The application crashed or failed to start.
    echo Please check the error message above.
    pause
)

endlocal
