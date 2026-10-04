@echo off
title Household Intelligence - PropTech SaaS Platform
cd /d "%~dp0"

echo ========================================================
echo   HOUSEHOLD INTELLIGENCE // PROPTECH AVM AND DEAL RADAR
echo   Linear Midnight Precision Instrument Design System
echo ========================================================
echo.

if not exist .venv\Scripts\python.exe goto :no_venv

echo Starting FastAPI Backend and Modern SPA on http://localhost:8080 ...
echo Close this window or press Ctrl+C to stop the server.
echo.

start "" "http://localhost:8080"
".venv\Scripts\python.exe" -m uvicorn backend.server:app --host 0.0.0.0 --port 8080 --reload
pause
exit /b 0

:no_venv
echo [ERROR] Virtual environment not found in .venv directory.
echo Please create the virtual environment and install dependencies.
pause
exit /b 1
