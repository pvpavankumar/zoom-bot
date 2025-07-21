@echo off
title Zoom Interview Bot - Windows Startup
color 0A

echo.
echo  ██████╗ ██████╗  ██████╗ ███╗   ███╗    ██████╗  ██████╗ ████████╗
echo ╚══███╔╝██╔═══██╗██╔═══██╗████╗ ████║    ██╔══██╗██╔═══██╗╚══██╔══╝
echo   ███╔╝ ██║   ██║██║   ██║██╔████╔██║    ██████╔╝██║   ██║   ██║   
echo  ███╔╝  ██║   ██║██║   ██║██║╚██╔╝██║    ██╔══██╗██║   ██║   ██║   
echo ███████╗╚██████╔╝╚██████╔╝██║ ╚═╝ ██║    ██████╔╝╚██████╔╝   ██║   
echo ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝    ╚═════╝  ╚═════╝    ╚═╝   
echo.
echo                    🤖 INTERVIEW ASSISTANT v1.0 🤖
echo                        Windows Compatible Edition
echo.

echo ==========================================
echo Starting Zoom Interview Bot Components
echo ==========================================

echo.
echo 🔍 Checking system status...

REM Check Redis
echo [1/4] Testing Redis...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis not running. Starting Redis...
    start "Redis Server" redis-server
    timeout /t 3 /nobreak >nul
) else (
    echo ✅ Redis is running
)

REM Check Python environment
echo [2/4] Testing Python environment...
python -c "print('✅ Python environment ready')" 2>nul
if errorlevel 1 (
    echo ❌ Python environment issue
    pause
    exit /b 1
)

REM Check dependencies
echo [3/4] Testing core dependencies...
python -c "import speech_recognition, sounddevice, redis; print('✅ All dependencies loaded')" 2>nul
if errorlevel 1 (
    echo ❌ Missing dependencies. Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [4/4] Testing Celery configuration...
python -c "from src.tasks.celery_app import celery_app; print('✅ Celery configured for Windows')" 2>nul
if errorlevel 1 (
    echo ❌ Celery configuration issue
    pause
    exit /b 1
)

echo.
echo ✅ All systems ready!
echo.

echo ==========================================
echo Choose startup mode:
echo ==========================================
echo.
echo [1] Start FULL BOT (Main app + Celery worker)
echo [2] Start MAIN APP only (FastAPI server)
echo [3] Start CELERY WORKER only (Windows compatible)
echo [4] Run SYSTEM CHECK
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto full_start
if "%choice%"=="2" goto main_only
if "%choice%"=="3" goto celery_only
if "%choice%"=="4" goto system_check
if "%choice%"=="5" goto end

:full_start
echo.
echo 🚀 Starting Full Zoom Interview Bot...
echo.
echo Starting Celery worker (Multithreaded mode)...
start "Celery Worker" cmd /k "celery -A src.tasks.celery_app worker --pool=threads --concurrency=4 --loglevel=info"
timeout /t 3 /nobreak >nul

echo Starting main application...
python -m src.main
goto end

:main_only
echo.
echo 🌐 Starting Main Application (FastAPI server)...
python -m src.main
goto end

:celery_only
echo.
echo ⚙️ Starting Celery Worker (Multithreaded mode)...
celery -A src.tasks.celery_app worker --pool=threads --concurrency=4 --loglevel=info
goto end

:system_check
echo.
echo 🔍 Running comprehensive system check...
python test_system_status.py
pause
goto end

:end
echo.
echo 👋 Zoom Interview Bot session ended.
pause
