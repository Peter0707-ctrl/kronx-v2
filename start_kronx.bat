@echo off
title Kronx Launcher
echo Starting Kronx AI Companion...
echo.

echo [1/2] Starting Backend on port 8000...
start "Kronx Backend" cmd /k "cd /d C:\Users\admin\Desktop\Kron-X\backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

timeout /t 6 /nobreak > nul

echo [2/2] Starting Frontend on port 3000...
start "Kronx Frontend" cmd /k "cd /d C:\Users\admin\Desktop\Kron-X\frontend && npm run dev"

timeout /t 8 /nobreak > nul

echo Opening browser...
start "" "http://localhost:3000"

echo.
echo Kronx is running!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000