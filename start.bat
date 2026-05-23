@echo off
title Vehicle Maintenance Prediction System — VMPS
color 0B
echo.
echo  =====================================================
echo   VMPS — Vehicle Maintenance Prediction System
echo   AI-Powered   Flask   scikit-learn   SQLite
echo  =====================================================
echo.
cd /d "%~dp0"
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org
    pause & exit /b 1
)
echo [2/3] Installing dependencies...
pip install -r requirements.txt --quiet
echo [3/3] Launching VMPS...
echo.
echo  App URL: http://localhost:5000
echo  Login:   admin@vmps.ai / admin123
echo.
python app.py
pause
