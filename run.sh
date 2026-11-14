#!/usr/bin/env bash
# ===============================================================================
#   IARFMS: Integrated Airline Reservation and Flight Management System
#   Group 4 DBMS Capstone Project (Experiments 1 - 7)
# ===============================================================================

set -e

echo "==============================================================================="
echo "  IARFMS: Integrated Airline Reservation and Flight Management System"
echo "  Group 4 DBMS Capstone Project (Experiments 1 - 7)"
echo "==============================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python 3 is not found in PATH! Please install Python 3.10+."
        exit 1
    else
        PY_CMD="python"
    fi
else
    PY_CMD="python3"
fi

# 2. Check dependencies
echo "[INFO] Verifying Python dependencies..."
$PY_CMD -c "import rich, tabulate, networkx, pytest" 2>/dev/null || {
    echo "[INFO] Installing required libraries from requirements.txt..."
    $PY_CMD -m pip install -r requirements.txt
}

echo ""
echo "[INFO] Launching Interactive Evaluation Dashboard..."
$PY_CMD app/cli_dashboard.py
