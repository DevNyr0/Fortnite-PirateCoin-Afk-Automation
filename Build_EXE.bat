@echo off
title Nyr0 Pirate Coin Automation - Build Standalone EXE
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --noconsole --onefile --icon "icon.ico" --add-data "web;web" --add-data "images;images" --add-data "icon.ico;." --add-data "logo.png;." --name "Nyr0 Pirate Coin Automation" main.py
if errorlevel 1 (
    echo.
    echo Build failed. Check errors above.
    pause
    exit /b 1
)
if exist "dist\Nyr0 Pirate Coin Automation.exe" (
    copy /y "dist\Nyr0 Pirate Coin Automation.exe" "Nyr0 Pirate Coin Automation.exe" >nul
)
echo.
echo ======================================================
echo Build complete: "Nyr0 Pirate Coin Automation.exe"
echo ======================================================
pause

