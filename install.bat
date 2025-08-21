@echo off
REM Simple installer script for Windows users

echo ========================================
echo Telegram Moderation Bot - Easy Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found! Checking version...
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.8+ is required.
    echo Please update your Python installation.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv bot_env
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call bot_env\Scripts\activate.bat

echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo Creating directories...
mkdir config >nul 2>&1
mkdir models >nul 2>&1
mkdir logs >nul 2>&1
mkdir data >nul 2>&1

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To start the bot, run: start_bot.bat
echo Or double-click start_bot.bat
echo.
echo The first time you run it, you'll need:
echo 1. A Telegram bot token from @BotFather
echo 2. To add your bot to channels as admin
echo.
echo Press any key to exit...
pause >nul