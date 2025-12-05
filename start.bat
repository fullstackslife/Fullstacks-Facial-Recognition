@echo off
REM Face Detection & Analysis System - Startup Script for Windows

echo 🎥 Starting Face Detection & Analysis System...

REM Check if Python 3 is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo 📦 Checking dependencies...
python -c "import cv2, flask" 2>nul
if errorlevel 1 (
    echo ⚠️  Some dependencies are missing. Installing...
    pip install -r requirements.txt
)

REM Get port from environment or use default
if "%PORT%"=="" set PORT=8080
if "%HOST%"=="" set HOST=0.0.0.0

echo 🚀 Starting server on http://%HOST%:%PORT%
echo 📱 Open your browser and navigate to: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
python app.py

pause

