@echo off
REM Windows launcher script for the Telegram Moderation Bot

echo Starting Telegram Moderation Bot...

REM Check if virtual environment exists
if exist bot_env\Scripts\activate.bat (
    echo Using virtual environment...
    call bot_env\Scripts\activate.bat
    python start_bot.py
) else (
    echo No virtual environment found, using system Python...
    python start_bot.py
)

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start the bot.
    echo Please make sure you've run install.bat first.
    echo.
    pause
)