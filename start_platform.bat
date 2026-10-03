@echo off
title Household Intelligence - PropTech SaaS Platform
echo ========================================================
echo   HOUSEHOLD INTELLIGENCE // PROPTECH AVM & DEAL RADAR
echo   Linear Midnight Precision Instrument Design System
echo ========================================================
echo.
echo Starting FastAPI Backend & Modern SPA on http://localhost:8000 ...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
start http://localhost:8000
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
pause
