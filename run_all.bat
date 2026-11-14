@echo off
echo ============================================================================
echo   IARFMS - Integrated Airline Reservation & Flight Management System
echo   Running Automated End-to-End Verification Suite (Experiments 1 - 7)
echo ============================================================================
cd /d "%~dp0"
python -m pytest tests/test_all_experiments.py -v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Verification suite encountered failures.
    exit /b 1
)
echo.
echo [SUCCESS] All 7 DBMS Experiments Verified Successfully!
echo To launch the interactive professor demonstration dashboard, run:
echo     python app/cli_dashboard.py
pause
