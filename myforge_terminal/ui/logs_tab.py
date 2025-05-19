"""
File: myforge_terminal/ui/logs_tab.py
Description: Logs Tab Module - Display and manage application logs

Structure:
  Classes:
    LogsTab:
      Description: Initialize logs tab
      - __init__(self, notebook, logger, theme_manager)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os

from utils.ui_utils import ContextMenu

class LogsTab:
    def __init__(self, notebook, logger, theme_manager):
        """Initialize logs tab"""
        self.notebook = notebook
        self.logger = logger
        self.theme_manager = theme_manager
        
        # Create frame for logs tab
        self.frame = tk.Frame(notebook, bg=theme_manager.bg_color)
        
        # Set up UI
        self._setup_ui()
        
        # Load logs
        self._load_logs()
        
        # Set up log observer
        self.logger.set_callback(self._on_log_added)
    
    def _setup_ui(self):
        """Set up logs tab UI"""
        logs_inner = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        logs_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Filter frame
        filter_frame = tk.Frame(logs_inner, bg=self.theme_manager.bg_color)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            filter_frame, text="Filter:", 
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
        ).pack(side=tk.LEFT, padx=5)
        
        self.filter_var = tk.StringVar()
        filter_entry = tk.Entry(
            filter_frame, textvariable=self.filter_var,
            bg="#2d2d2d", fg=self.theme_manager.fg_color
        )
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        filter_entry.bind("<KeyRelease>", self._apply_filter)
        
        ttk.Button(
            filter_frame, text="Clear Filter", 
            command=self._clear_filter
        ).pack(side=tk.LEFT, padx=5)
        
        # Logs output
        self.logs_output = scrolledtext.ScrolledText(
            logs_inner, wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#2d2d2d", fg=self.theme_manager.fg_color,
            insertbackground=self.theme_manager.fg_color
        )
        self.logs_output.pack(fill=tk.BOTH, expand=True)
        
        # Set read-only
        self.logs_output.config(state=tk.DISABLED)
        
        # Create context menu
        self.context_menu = ContextMenu(self.logs_output, self.theme_manager)
        self.context_menu.add_command("Copy", self._copy_selected)
        self.context_menu.add_command("Select All", self._select_all)
        self.context_menu.add_command("Clear", self._clear_logs)
        
        # Action buttons
        btn_frame = tk.Frame(logs_inner, bg=self.theme_manager.bg_color)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            btn_frame, text="Clear Logs", 
            command=self._clear_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="Export Logs", 
            command=self._export_logs
        ).pack(side=tk.LEFT, padx=5)
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            btn_frame, text="Auto-scroll",
            variable=self.auto_scroll_var,
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).pack(side=tk.RIGHT, padx=5)
    
    def _load_logs(self):
        """Load logs from logger"""
        self.logs_output.config(state=tk.NORMAL)
        self.logs_output.delete(1.0, tk.END)
        
        # Get all logs
        logs = self.logger.get_logs()
        
        # Insert logs
        for log in logs:
            self.logs_output.insert(tk.END, log + "\n")
        
        # Auto-scroll to end
        self.logs_output.see(tk.END)
        
        self.logs_output.config(state=tk.DISABLED)
    
    def _on_log_added(self, log_entry):
        """Handle new log entry"""
        if not hasattr(self, 'logs_output') or not self.logs_output.winfo_exists():
            return
        
        try:
            self.logs_output.config(state=tk.NORMAL)
            self.logs_output.insert(tk.END, log_entry + "\n")
            
            # Apply filter
            if self.filter_var.get():
                self._apply_filter()
            
            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.logs_output.see(tk.END)
            
            self.logs_output.config(state=tk.DISABLED)
        except tk.TclError:
            # Widget might be destroyed
            pass
    
    def _apply_filter(self, event=None):
        """Apply filter to logs"""
        filter_text = self.filter_var.get().lower()
        
        if not filter_text:
            self._load_logs()
            return
        
        # Get all logs
        logs = self.logger.get_logs()
        
        # Filter logs
        filtered_logs = [log for log in logs if filter_text in log.lower()]
        
        # Update display
        self.logs_output.config(state=tk.NORMAL)
        self.logs_output.delete(1.0, tk.END)
        
        for log in filtered_logs:
            self.logs_output.insert(tk.END, log + "\n")
        
        # Auto-scroll to end
        self.logs_output.see(tk.END)
        
        self.logs_output.config(state=tk.DISABLED)
    
    def _clear_filter(self):
        """Clear filter"""
        self.filter_var.set("")
        self._load_logs()
    
    def _copy_selected(self):
        """Copy selected text to clipboard"""
        try:
            selected_text = self.logs_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.frame.clipboard_clear()
            self.frame.clipboard_append(selected_text)
        except tk.TclError:
            pass  # No selection
    
    def _select_all(self):
        """Select all text in logs"""
        self.logs_output.tag_add(tk.SEL, "1.0", tk.END)
        self.logs_output.mark_set(tk.INSERT, "1.0")
        self.logs_output.see(tk.INSERT)
    
    def _clear_logs(self):
        """Clear logs"""
        if not messagebox.askyesno(
            "Clear Logs",
            "Are you sure you want to clear all logs from the display?"
        ):
            return
        
        self.logs_output.config(state=tk.NORMAL)
        self.logs_output.delete(1.0, tk.END)
        self.logs_output.config(state=tk.DISABLED)
        
        # Log the clearing
        self.logger.log("Logs cleared from display")
        
        # Ask about clearing log file
        if messagebox.askyesno(
            "Clear Log File",
            "Do you also want to clear the log file? This cannot be undone."
        ):
            # Clear log file
            if self.logger.clear_log_file():
                messagebox.showinfo(
                    "Log File Cleared",
                    "The log file has been cleared."
                )
            else:
                messagebox.showerror(
                    "Error",
                    "Could not clear log file."
                )
    
    def _export_logs(self):
        """Export logs to a file"""
        filename = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".log",
            filetypes=(
                ("Log Files", "*.log"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            )
        )
        
        if not filename:
            return
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.logs_output.get(1.0, tk.END))
            
            messagebox.showinfo(
                "Export Logs",
                f"Logs exported successfully to {filename}"
            )
            
            self.logger.log(f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error exporting logs: {e}"
            )
            
            self.logger.log(f"Error exporting logs: {e}")