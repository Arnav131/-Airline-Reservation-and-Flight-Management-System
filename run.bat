@echo off
setlocal enabledelayedexpansion

title IARFMS - Airline Reservation and Flight Management System (Group 4)
cls

echo ===============================================================================
echo   IARFMS: Integrated Airline Reservation and Flight Management System
echo   Group 4 DBMS Capstone Project (Experiments 1 - 7)
echo ===============================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Ensure core dependencies are installed
echo [INFO] Verifying Python dependencies (rich, tabulate, networkx, pytest)...
python -c "import rich, tabulate, networkx, pytest" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing required libraries from requirements.txt...
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Dependency installation encountered warnings, proceeding...
    )
)

echo.
echo [INFO] Launching Interactive Evaluation Dashboard...
python app/cli_dashboard.py

pause
