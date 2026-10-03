@echo off
title Jabodetabek Rental Intelligence Dashboard
cd /d "%~dp0"

echo ===================================================
echo Membuka Jabodetabek Rental Intelligence Dashboard...
echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) belum ada.
    echo Silakan install dependencies terlebih dahulu.
    pause
    exit /b 1
)

echo Menjalankan aplikasi Streamlit...
echo Buka browser di http://localhost:8501 jika tidak terbuka otomatis.
echo Tekan Ctrl+C di jendela ini jika ingin menutup aplikasi.
echo.

".venv\Scripts\python.exe" -m streamlit run app.py

pause
