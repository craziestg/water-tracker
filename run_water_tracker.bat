@echo off
REM Water Tracker Launcher
REM This batch file launches the Water Tracker app
REM You can create a shortcut to this file on your desktop for quick access

REM Get the directory where this batch file is located
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"

REM Launch the Python app
python "%SCRIPT_DIR%water_tracker.py"

REM If there's an error, pause so you can see the message
if errorlevel 1 (
    echo.
    echo Error: Could not launch Water Tracker
    echo Make sure Python 3.6+ is installed and in your PATH
    pause
)
