"""
File: myforge_terminal/utils/logger.py
Description: Logger Module - Log application events

Structure:
  Classes:
    Logger:
      Description: Application logger
      - __init__(self, filename='ssh_terminal.log')
      - log(self, message)
      - get_logs(self)
      - set_callback(self, callback)
      - clear_log_file(self)
"""

import os
from datetime import datetime
import threading

class Logger:
    """Application logger"""
    
    def __init__(self, filename="ssh_terminal.log"):
        """Initialize logger"""
        self.filename = filename
        self.logs = []
        self.max_memory_logs = 1000  # Maximum number of log entries to keep in memory
        self.callback = None
        self.callback_lock = threading.Lock()
        
        # Load existing logs (last N entries)
        self._load_recent_logs()
    
    def log(self, message):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Add to in-memory logs
        self.logs.append(log_entry)
        
        # Trim logs if too many
        if len(self.logs) > self.max_memory_logs:
            self.logs = self.logs[-self.max_memory_logs:]
        
        # Write to file
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # Notify callback if set
        with self.callback_lock:
            if self.callback:
                try:
                    self.callback(log_entry)
                except Exception as e:
                    print(f"Error in log callback: {e}")
    
    def get_logs(self):
        """Get all logs in memory"""
        return self.logs
    
    def set_callback(self, callback):
        """Set callback for new log entries"""
        with self.callback_lock:
            self.callback = callback
    
    def clear_log_file(self):
        """Clear log file"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("")
            
            # Add a log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] Log file cleared"
            
            # Add to in-memory logs
            self.logs = [log_entry]
            
            # Write to file
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
            
            # Notify callback if set
            with self.callback_lock:
                if self.callback:
                    try:
                        self.callback(log_entry)
                    except Exception as e:
                        print(f"Error in log callback: {e}")
            
            return True
        except Exception as e:
            print(f"Error clearing log file: {e}")
            return False
    
    def _load_recent_logs(self):
        """Load recent logs from file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8", errors="replace") as f:
                    # Read last N lines
                    lines = f.readlines()
                    self.logs = [line.strip() for line in lines[-self.max_memory_logs:]]
        except Exception as e:
            print(f"Error loading log file: {e}")
            self.logs = []