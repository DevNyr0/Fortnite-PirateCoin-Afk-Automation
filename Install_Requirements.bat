@echo off
title Nyr0 Pirate Coin Automation - Install Requirements
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo ======================================================
echo Installation finished.
echo ======================================================
pause

