@echo off
title Jabodetabek Rental Intelligence Dashboard
cd /d "%~dp0"

echo ===================================================
echo Opening Jabodetabek Rental Intelligence Dashboard...
echo ===================================================
echo.

if not exist .venv\Scripts\python.exe goto :no_venv

echo Starting Streamlit application...
echo Open browser at http://localhost:8501 if it does not launch automatically.
echo Press Ctrl+C in this terminal window to terminate the application.
echo.

".venv\Scripts\python.exe" -m streamlit run app.py
pause
exit /b 0

:no_venv
echo [ERROR] Virtual environment not found in .venv directory.
echo Please install dependencies first.
pause
exit /b 1
