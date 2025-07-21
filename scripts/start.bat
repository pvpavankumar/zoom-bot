@echo off
echo =============================================================
echo Starting Zoom Interview Bot
echo =============================================================
echo.

REM Change to project root
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo 💡 Run: python -m venv .venv
    echo 💡 Then: scripts\install_modern_audio.bat
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo 🤖 Starting Zoom Interview Bot...
echo 🎵 Modern audio processing enabled
echo 🌐 Starting FastAPI server...
echo.

REM Start the application with correct entry point
python -m src.main

echo.
echo 🛑 Bot stopped
pause
