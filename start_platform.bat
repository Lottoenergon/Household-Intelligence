@echo off
title Household Intelligence - PropTech SaaS Platform
cd /d "%~dp0"

echo ========================================================
echo   HOUSEHOLD INTELLIGENCE // PROPTECH AVM & DEAL RADAR
echo   Linear Midnight Precision Instrument Design System
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please install dependencies first.
    pause
    exit /b 1
)

echo Starting FastAPI Backend & Modern SPA on http://localhost:8080 ...
echo.
start "" http://localhost:8080
".venv\Scripts\python.exe" -m uvicorn backend.server:app --host 0.0.0.0 --port 8080 --reload
pause
