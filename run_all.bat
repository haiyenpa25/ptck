@echo off
title CW-Quant System Launcher
echo ==========================================
echo    🏦 CW-QUANT TERMINAL - ALL-IN-ONE
echo ==========================================
echo.

echo [1/2] Creating/Updating Database structure...
python -c "from src.core.database import init_db; init_db('cw_quant.db')"

echo [2/2] Starting Core Engine (Signal Processor)...
start "CW-Quant ENGINE" cmd /k "python -m src.main"

echo [3/3] Starting Streamlit Dashboard...
echo Dashboard will open in your browser shortly...
python -m streamlit run dashboard/app.py

pause
