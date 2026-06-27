@echo off
title Kronx AI Companion
color 0A

echo.
echo  ██╗  ██╗██████╗  ██████╗ ███╗   ██╗██╗  ██╗
echo  ██║ ██╔╝██╔══██╗██╔═══██╗████╗  ██║╚██╗██╔╝
echo  █████╔╝ ██████╔╝██║   ██║██╔██╗ ██║ ╚███╔╝
echo  ██╔═██╗ ██╔══██╗██║   ██║██║╚██╗██║ ██╔██╗
echo  ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║██╔╝ ██╗
echo  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
echo.
echo  Starting Kronx AI Companion...
echo  ================================
echo.

:: Start Backend
echo  [1/2] Starting Backend...
start "Kronx Backend" cmd /k "cd /d C:\Users\admin\Desktop\Kron-X\backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: Wait for backend to start
echo  Waiting for backend...
timeout /t 5 /nobreak > nul

:: Start Frontend
echo  [2/2] Starting Frontend...
start "Kronx Frontend" cmd /k "cd /d C:\Users\admin\Desktop\Kron-X\frontend && npm run dev"

:: Wait for frontend to start
echo  Waiting for frontend...
timeout /t 8 /nobreak > nul

:: Open browser
echo  Opening Kronx in browser...
start "" "http://localhost:3000"

echo.
echo  ================================
echo  Kronx is running!
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000
echo  ================================
echo.
echo  Close this window anytime.
pause