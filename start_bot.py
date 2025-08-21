#!/usr/bin/env python3
"""
Simple launcher script for the Telegram Moderation Bot.
This makes it easy for non-technical users to start the application.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import subprocess

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        messagebox.showerror(
            "Python Version Error",
            "This application requires Python 3.8 or higher.\n"
            f"You are running Python {sys.version_info.major}.{sys.version_info.minor}.\n\n"
            "Please install a newer version of Python."
        )
        return False
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import telegram
        import yaml
        import PIL
        return True
    except ImportError as e:
        missing_module = str(e).split("'")[1]
        
        result = messagebox.askyesno(
            "Missing Dependencies",
            f"Required module '{missing_module}' is not installed.\n\n"
            "Would you like to install the required dependencies now?\n\n"
            "This will run: pip install -r requirements.txt"
        )
        
        if result:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                messagebox.showinfo("Success", "Dependencies installed successfully!")
                return True
            except subprocess.CalledProcessError as e:
                messagebox.showerror(
                    "Installation Failed",
                    f"Failed to install dependencies:\n{e}\n\n"
                    "Please try running this command manually:\n"
                    "pip install -r requirements.txt"
                )
                return False
        return False

def create_directories():
    """Create necessary directories."""
    dirs = ["config", "models", "logs", "data"]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

def show_welcome():
    """Show welcome message for first-time users."""
    welcome_text = """
Welcome to Telegram Moderation Bot!

This application helps you automatically monitor and moderate your Telegram channels.

What this bot can do:
✓ Detect spam messages
✓ Block inappropriate content
✓ Remove harassment and bullying
✓ Filter adult content
✓ Monitor image and video content

To get started:
1. Get a bot token from @BotFather on Telegram
2. Configure your moderation settings
3. Add the bot to your channels as an admin
4. Let it protect your community!

Click OK to open the main application.
    """
    
    messagebox.showinfo("Welcome to Telegram Moderation Bot", welcome_text.strip())

def main():
    """Main launcher function."""
    # Create a temporary root window for message boxes
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        # Check Python version
        if not check_python_version():
            return
        
        # Create necessary directories
        create_directories()
        
        # Check if this is first run
        if not os.path.exists("gui_settings.json"):
            show_welcome()
        
        # Check dependencies
        if not check_dependencies():
            return
        
        # Start the main GUI application
        from gui import ModBotGUI
        root.destroy()  # Close the temporary window
        
        app = ModBotGUI()
        app.run()
        
    except Exception as e:
        messagebox.showerror(
            "Startup Error",
            f"Failed to start the application:\n\n{e}\n\n"
            "Please check that all files are present and try again."
        )
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()