@echo off
echo ==========================================
echo   AI Instagram Automation System
echo   Starting server...
echo ==========================================
echo.

:: Check Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing Python dependencies...
py -m pip install -r backend\requirements.txt --quiet

:: Create .env if not exists
if not exist ".env" (
    echo [2/3] Creating .env config file...
    copy .env.example .env
    echo.
    echo ** IMPORTANT: Edit .env file with your credentials **
    echo    OR configure via the dashboard Settings page
    echo.
)

:: Start the server
echo [3/3] Starting backend server...
echo.
echo Dashboard: http://localhost:8000
echo.
echo Press Ctrl+C to stop.
echo.

cd backend
py main.py

pause
