@echo off
echo ========================================
echo   MediRecord - Patient Record System
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    pause
    exit /b
)

REM Install dependencies
echo Installing required packages...
pip install -r requirements.txt --quiet

echo.
echo Starting server...
echo Open your browser at: http://127.0.0.1:5000
echo Press CTRL+C to stop.
echo.
python app.py
pause
