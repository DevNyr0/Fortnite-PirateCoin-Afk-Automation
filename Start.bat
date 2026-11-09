@echo off
title Nyr0 Pirate Coin Automation
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Program encountered an issue.
    pause
)

