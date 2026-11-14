@echo off
title Global Airdrop Hunter Launcher

echo ========================================
echo   Global Airdrop Hunter - Quick Start
echo ========================================
echo.
echo Starting application in browser app mode...
echo This will open Microsoft Edge in a chromeless window.
echo.
echo IMPORTANT: Keep this console window OPEN while using the app.
echo Close the Edge window to stop the application.
echo.

powershell -ExecutionPolicy Bypass -File "scripts\launch.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start application.
    echo Make sure you have run .\scripts\setup.ps1 first.
    echo.
    pause
)