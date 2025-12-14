@echo off
echo ========================================
echo    Job Tracker - Quick Start
echo ========================================
echo.
echo Starting Backend and Frontend servers...
echo.

REM Start backend in a new window
start "Job Tracker Backend" cmd /k "cd logic && venv\Scripts\activate && python -m uvicorn app.main:app"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "Job Tracker Frontend" cmd /k "cd view && echo Starting Frontend Development Server... && npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.
echo Two new windows have been opened.
echo Close this window or press any key to exit.
echo.
pause
