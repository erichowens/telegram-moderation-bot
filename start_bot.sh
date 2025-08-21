#!/bin/bash

# Mac/Linux launcher script for the Telegram Moderation Bot

echo "Starting Telegram Moderation Bot..."

# Check if virtual environment exists
if [ -d "bot_env" ] && [ -f "bot_env/bin/activate" ]; then
    echo "Using virtual environment..."
    source bot_env/bin/activate
    python3 start_bot.py
else
    echo "No virtual environment found, using system Python..."
    python3 start_bot.py
fi

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Failed to start the bot."
    echo "Please make sure you've run ./install.sh first."
    echo
    echo "Press Enter to continue..."
    read
fi