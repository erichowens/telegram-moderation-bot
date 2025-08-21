#!/bin/bash

# Simple installer script for Mac/Linux users

echo "========================================"
echo "Telegram Moderation Bot - Easy Setup"
echo "========================================"
echo

echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.8+ from https://python.org/downloads"
    echo "Or use your system package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "Python found! Checking version..."
python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3.8+ is required."
    echo "Please update your Python installation."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv bot_env
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment."
    echo "You may need to install python3-venv:"
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    exit 1
fi

echo "Activating virtual environment..."
source bot_env/bin/activate

echo "Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    echo "Please check your internet connection and try again."
    exit 1
fi

echo "Creating directories..."
mkdir -p config models logs data

echo "Making scripts executable..."
chmod +x start_bot.sh

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "To start the bot, run: ./start_bot.sh"
echo "Or double-click start_bot.sh (if GUI file manager supports it)"
echo
echo "The first time you run it, you'll need:"
echo "1. A Telegram bot token from @BotFather"
echo "2. To add your bot to channels as admin"
echo
echo "Press Enter to continue..."
read