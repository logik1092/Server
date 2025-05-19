#!/usr/bin/env python3
"""
File: myforge_terminal/main.py
Description: MyForge SSH Terminal - Main Entry Point

Structure:
  Functions:
    - check_dependencies()
    - main()
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from ui.main_window import MainWindow
from utils.config import Config
from utils.logger import Logger

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import paramiko
        return True
    except ImportError:
        messagebox.showerror(
            "Missing Dependencies",
            "Required package 'paramiko' is not installed.\n\n"
            "Please install it using:\n"
            "pip install paramiko"
        )
        return False

def main():
    """Main entry point for the application"""
    if not check_dependencies():
        return

    # Create root window
    root = tk.Tk()
    root.title("MyForge SSH Terminal")
    
    # Initialize config and logger
    config = Config()
    logger = Logger()
    
    # Create main application window
    app = MainWindow(root, config, logger)
    
    # Start the main event loop
    root.mainloop()
    
    # Save config on exit
    config.save()
    
if __name__ == "__main__":
    main()