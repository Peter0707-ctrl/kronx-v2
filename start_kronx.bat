@echo off
title Kronx AI Companion Launcher
echo ========================================================
echo               KRONX AI COMPANION (LOW-RAM)
echo ========================================================
echo.

set KRONX_DIR=%~dp0
set KRONX_DIR=%KRONX_DIR:~0,-1%

echo [1/2] Starting Backend API (Port 8000)...
start "Kronx Backend API" cmd /k "cd /d "%KRONX_DIR%\backend" && uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 4 /nobreak > nul

echo [2/2] Starting Frontend UI (Port 3000)...
start "Kronx Web UI" cmd /k "cd /d "%KRONX_DIR%\frontend" && (if exist .next rmdir /s /q .next) && npm run dev"


timeout /t 5 /nobreak > nul

echo.
echo Launching Browser...
start "" "http://localhost:3000"

echo.
echo ========================================================
echo Kronx is active!
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo System Status: http://localhost:8000/api/system/status
echo ========================================================