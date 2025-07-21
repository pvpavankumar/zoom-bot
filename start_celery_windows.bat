@echo off
echo ==========================================
echo Starting Celery Worker with Threads
echo ==========================================

echo.
echo Stopping any existing Celery processes...
taskkill /f /im celery.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq celery*" 2>nul

echo.
echo Starting Celery worker with multithreaded settings...
echo Pool: threads (multithreaded, high performance)
echo Concurrency: 4 (concurrent task processing)
echo.

REM Start Celery with threaded settings for better performance
celery -A src.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4

echo.
echo Celery worker stopped.
pause
