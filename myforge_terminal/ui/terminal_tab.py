"""
File: myforge_terminal/ui/terminal_tab.py
Description: Terminal Tab Module - Terminal functionality for SSH connections

Structure:
  Classes:
    TerminalTab:
      Description: Initialize terminal tab
      - __init__(self, notebook, ssh_client, config, logger, theme_manager)
      - append_output(self, text)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import re
import threading
import time

from utils.ui_utils import ContextMenu

class TerminalTab:
    def __init__(self, notebook, ssh_client, config, logger, theme_manager):
        """Initialize terminal tab"""
        self.notebook = notebook
        self.ssh_client = ssh_client
        self.config = config
        self.logger = logger
        self.theme_manager = theme_manager
        
        # Create frame for terminal tab
        self.frame = tk.Frame(notebook, bg=theme_manager.bg_color)
        
        # Commands history
        self.command_history = []
        self.history_index = 0
        
        # Process tracking
        self.running_processes = {}
        
        # Set up UI elements
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up terminal tab UI"""
        # Command categories for quick access
        self._setup_command_categories()
        
        # Terminal output
        self.output = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD,
            font=("Consolas", self.config.get("font_size", 10)),
            bg="#2d2d2d", fg=self.theme_manager.fg_color,
            insertbackground=self.theme_manager.fg_color
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create context menu
        self.context_menu = ContextMenu(self.output, self.theme_manager)
        self.context_menu.add_command("Copy", self._copy_selected)
        self.context_menu.add_command("Select All", self._select_all)
        self.context_menu.add_command("Clear", self._clear_terminal)
        
        # Running processes frame
        self.processes_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        self.processes_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        tk.Label(self.processes_frame, text="Running Processes:", 
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color).pack(side=tk.LEFT)
        
        # Process indicators
        self.uvicorn_indicator = tk.Label(
            self.processes_frame, text="Uvicorn: Stopped", 
            bg=self.theme_manager.bg_color, fg="#ff7777", padx=5
        )
        self.uvicorn_indicator.pack(side=tk.LEFT, padx=10)
        
        self.llama_indicator = tk.Label(
            self.processes_frame, text="LLaMA: Stopped", 
            bg=self.theme_manager.bg_color, fg="#ff7777", padx=5
        )
        self.llama_indicator.pack(side=tk.LEFT, padx=10)
        
        # Command entry frame
        cmd_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(cmd_frame, text="Command:", 
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color).pack(side=tk.LEFT, padx=5)
        
        self.cmd_entry = tk.Entry(
            cmd_frame, font=("Consolas", self.config.get("font_size", 10)),
            bg="#2d2d2d", fg=self.theme_manager.fg_color, 
            insertbackground=self.theme_manager.fg_color
        )
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Bind key events to command entry
        self.cmd_entry.bind('<Return>', self._send_command)
        self.cmd_entry.bind('<Up>', self._get_previous_command)
        self.cmd_entry.bind('<Down>', self._get_next_command)
        self.cmd_entry.bind('<Tab>', self._tab_completion)
        
        ttk.Button(cmd_frame, text="Send", command=self._send_command).pack(side=tk.RIGHT, padx=5)
        
        # Quick command buttons
        self._setup_quick_buttons()
    
    def _setup_command_categories(self):
        """Set up command category buttons"""
        category_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        category_frame.pack(fill=tk.X, pady=(5, 0), padx=5)
        
        # Define command categories
        defined_categories = {
            "🚀 App": ["launch_llama", "activate_venv", "start_uvicorn", "kill_uvicorn"],
            "🌐 Nginx": ["reload_nginx", "restart_nginx", "nginx_status", "test_nginx"],
            "📂 Files": ["cd_website", "cd_nginx", "cd_home", "list_files"],
            "🖥️ System": ["check_memory", "check_disk", "check_cpu", "python_processes"]
        }
        
        # Create category buttons
        for cat_name, items_list in defined_categories.items():
            cat_btn = ttk.Menubutton(category_frame, text=cat_name)
            cat_btn.pack(side=tk.LEFT, padx=5)
            
            cat_menu = tk.Menu(cat_btn, tearoff=0, bg="#2d2d2d", fg=self.theme_manager.fg_color)
            cat_btn["menu"] = cat_menu
            
            for item in items_list:
                cmd_key = item
                display_name = cmd_key.replace('_', ' ').title()
                
                commands = self.config.get("commands", {})
                if cmd_key in commands:
                    cmd_str = commands[cmd_key]
                    cat_menu.add_command(
                        label=display_name,
                        command=lambda cmd=cmd_str: self._inject_command(cmd)
                    )
                else:
                    cat_menu.add_command(
                        label=f"{display_name} (missing)",
                        state=tk.DISABLED
                    )
        
        # Add cheat sheet button
        ttk.Button(
            category_frame, text="📋 Cheat Sheet",
            command=self._show_cheat_sheet
        ).pack(side=tk.RIGHT, padx=5)
    
    def _setup_quick_buttons(self):
        """Set up quick access command buttons"""
        btn_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        btn_frame.pack(fill=tk.X, pady=5, padx=5)
        
        commands = self.config.get("commands", {})
        
        quick_buttons = [
            ("Launch LLaMA", commands.get("launch_llama", "")),
            ("Activate venv", commands.get("activate_venv", "")),
            ("Start Uvicorn", commands.get("start_uvicorn", "")),
            ("Kill Uvicorn", commands.get("kill_uvicorn", "")),
            ("CD Website", commands.get("cd_website", "")),
            ("List Files", commands.get("list_files", ""))
        ]
        
        for label, command in quick_buttons:
            if command:
                ttk.Button(
                    btn_frame, text=label,
                    command=lambda cmd=command: self._inject_command(cmd)
                ).pack(side=tk.LEFT, padx=2)
        
        # Background run button
        self.bg_btn = ttk.Menubutton(btn_frame, text="Run in Background")
        self.bg_btn.pack(side=tk.RIGHT, padx=5)
        
        self.bg_menu = tk.Menu(self.bg_btn, tearoff=0, bg="#2d2d2d", fg=self.theme_manager.fg_color)
        self.bg_btn["menu"] = self.bg_menu
        
        self.bg_menu.add_command(
            label="Run Python Script",
            command=lambda: self._inject_command("nohup python3 script.py &")
        )
        self.bg_menu.add_command(
            label="Run Uvicorn Server",
            command=lambda: self._inject_command(
                "nohup uvicorn server:app --host 0.0.0.0 --port=8080 &"
            )
        )
        self.bg_menu.add_separator()
        self.bg_menu.add_command(
            label="Custom Background Command...",
            command=self._run_custom_background
        )
    
    def _send_command(self, event=None):
        """Send command to SSH server"""
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return "break"
        
        # Special command processing
        if cmd.lower() == "clear":
            self._clear_terminal()
            self.cmd_entry.delete(0, tk.END)
            return "break"
        
        # Send command
        success = self.ssh_client.send_command(cmd)
        
        if success:
            # Add to command history
            if not self.command_history or self.command_history[-1] != cmd:
                self.command_history.append(cmd)
            
            self.history_index = len(self.command_history)
            
            # Check for process control
            self._check_for_process_start(cmd)
        
        # Clear entry
        self.cmd_entry.delete(0, tk.END)
        
        return "break"
    
    def _check_for_process_start(self, cmd):
        """Check if command starts a known process"""
        cmd_lower = cmd.lower()
        
        # Check for uvicorn
        if "uvicorn" in cmd_lower and "server" in cmd_lower:
            self.uvicorn_indicator.config(text="Uvicorn: Starting...", fg="#ffff77")
            
            # Schedule a check to update status
            self.frame.after(2000, self._check_uvicorn_status)
        
        # Check for llama
        elif "llama-server" in cmd_lower:
            self.llama_indicator.config(text="LLaMA: Starting...", fg="#ffff77")
            
            # Schedule a check to update status
            self.frame.after(2000, self._check_llama_status)
        
        # Check for kill commands
        elif "pkill" in cmd_lower or "kill" in cmd_lower:
            if "uvicorn" in cmd_lower or "python" in cmd_lower:
                self.uvicorn_indicator.config(text="Uvicorn: Stopped", fg="#ff7777")
            
            if "llama" in cmd_lower:
                self.llama_indicator.config(text="LLaMA: Stopped", fg="#ff7777")
    
    def _check_uvicorn_status(self):
        """Check if uvicorn process is running"""
        if not self.ssh_client.connected:
            self.uvicorn_indicator.config(text="Uvicorn: Unknown", fg="#aaaaaa")
            return
        
        # Send command to check for uvicorn processes
        self.ssh_client.send_command("ps aux | grep '[u]vicorn'")
        
        # Schedule a follow-up to check logs for response
        self.frame.after(1000, lambda: self._update_process_indicator(
            "Uvicorn", self.uvicorn_indicator, "uvicorn"
        ))
    
    def _check_llama_status(self):
        """Check if llama process is running"""
        if not self.ssh_client.connected:
            self.llama_indicator.config(text="LLaMA: Unknown", fg="#aaaaaa")
            return
        
        # Send command to check for llama processes
        self.ssh_client.send_command("ps aux | grep '[l]lama-server'")
        
        # Schedule a follow-up to check logs for response
        self.frame.after(1000, lambda: self._update_process_indicator(
            "LLaMA", self.llama_indicator, "llama-server"
        ))
    
    def _update_process_indicator(self, name, indicator, process_name):
        """Update process indicator based on recent output"""
        # Get last few lines from terminal output
        last_output = self.output.get("end-30l", "end")
        
        if process_name in last_output.lower():
            # Process is running
            indicator.config(text=f"{name}: Running", fg="#77ff77")
            
            # Look for PID
            pid_match = re.search(r'\s+(\d+)\s+', last_output)
            if pid_match:
                pid = pid_match.group(1)
                
                # Update with PID and kill button
                indicator.config(text=f"{name}: Running (PID: {pid})")
                
                # Create kill button if not exists
                kill_btn_name = f"{process_name}_kill_btn"
                if not hasattr(self, kill_btn_name):
                    kill_btn = ttk.Button(
                        self.processes_frame, text="Stop",
                        command=lambda p=pid: self._kill_process(process_name, p)
                    )
                    kill_btn.pack(side=tk.LEFT, padx=2)
                    setattr(self, kill_btn_name, kill_btn)
        else:
            # Process not running
            indicator.config(text=f"{name}: Stopped", fg="#ff7777")
            
            # Remove kill button if exists
            kill_btn_name = f"{process_name}_kill_btn"
            if hasattr(self, kill_btn_name):
                btn = getattr(self, kill_btn_name)
                btn.destroy()
                delattr(self, kill_btn_name)
    
    def _kill_process(self, process_name, pid):
        """Kill a running process"""
        if not self.ssh_client.connected:
            return
        
        if messagebox.askyesno(
            "Confirm", f"Stop {process_name} process (PID: {pid})?"
        ):
            self.ssh_client.send_command(f"kill-process:{pid}")
            
            # Update indicator
            if process_name == "uvicorn":
                self.uvicorn_indicator.config(text="Uvicorn: Stopping...", fg="#ffff77")
                self.frame.after(1000, self._check_uvicorn_status)
            elif process_name == "llama-server":
                self.llama_indicator.config(text="LLaMA: Stopping...", fg="#ffff77")
                self.frame.after(1000, self._check_llama_status)
    
    def _get_previous_command(self, event=None):
        """Get previous command from history"""
        if not self.command_history:
            return "break"
        
        if self.history_index > 0:
            self.history_index -= 1
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.command_history[self.history_index])
        
        return "break"
    
    def _get_next_command(self, event=None):
        """Get next command from history"""
        if not self.command_history:
            return "break"
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, self.command_history[self.history_index])
        else:
            # Clear when at the end of history
            self.history_index = len(self.command_history)
            self.cmd_entry.delete(0, tk.END)
        
        return "break"
    
    def _tab_completion(self, event=None):
        """Handle tab completion for commands"""
        if not self.ssh_client.connected:
            return "break"
        
        current_cmd = self.cmd_entry.get().lower()
        
        # Check for custom command completion
        commands = self.config.get("commands", {})
        for cmd_name in commands:
            display_name = cmd_name.replace('_', ' ')
            if display_name.startswith(current_cmd):
                self.cmd_entry.delete(0, tk.END)
                self.cmd_entry.insert(0, display_name)
                return "break"
        
        # Send actual tab character for path completion
        path_prefixes = ["/var/www/", "/etc/nginx/", "/home/", "/usr/local/bin/"]
        for prefix in path_prefixes:
            if current_cmd.startswith(prefix) or (current_cmd.startswith("cd ") and 
                                                 current_cmd[3:].startswith(prefix)):
                if self.ssh_client.shell:
                    self.ssh_client.shell.send("\t")
                break
        
        return "break"
    
    def _inject_command(self, cmd):
        """Insert a command into the entry and send it"""
        if not cmd:
            return
        
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self._send_command()
    
    def _run_custom_background(self):
        """Prompt for a custom background command"""
        cmd = simpledialog.askstring(
            "Background Command",
            "Enter command to run in background:",
            initialvalue="python3 script.py"
        )
        
        if not cmd:
            return
        
        # Format command to run in background
        if not cmd.startswith("nohup"):
            cmd = f"nohup {cmd}"
        
        if not cmd.endswith("&"):
            cmd = f"{cmd} &"
        
        self._inject_command(cmd)
    
    def _show_cheat_sheet(self):
        """Show command cheat sheet dialog"""
        from ui.dialogs import CheatSheetDialog
        
        cheat_sheet = CheatSheetDialog(
            self.frame, 
            self.config, 
            self.theme_manager, 
            self._inject_command
        )
    
    def append_output(self, text):
        """Append text to terminal output"""
        if not hasattr(self, 'output') or not self.output.winfo_exists():
            return
        
        self.output.config(state=tk.NORMAL)
        
        # Get current position
        current_pos = self.output.index(tk.END + "-1c")
        
        # Insert text
        self.output.insert(tk.END, text)
        
        # Apply syntax highlighting
        self._highlight_text(text, current_pos)
        
        # Auto-scroll
        self.output.see(tk.END)
        self.output.config(state=tk.NORMAL)  # Keep enabled for selection
    
    def _highlight_text(self, text, start_pos):
        """Apply syntax highlighting to text"""
        # Highlight prompts
        if "> " in text or "$ " in text or "# " in text:
            search_start_index = self.output.index(f"{start_pos} linestart")
            search_end_index = self.output.index(tk.END)
            
            prompt_patterns = [
                r"([a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+:[^$#\n]*[$#]\s)",
                r"(\w+@\w+:.*?[$#]\s)"
            ]
            
            for pattern in prompt_patterns:
                idx = search_start_index
                while True:
                    match_start = self.output.search(
                        pattern, idx, stopindex=search_end_index, regexp=True
                    )
                    if not match_start:
                        break
                    
                    match_end = f"{match_start}+{len(self.output.get(match_start, f'{match_start} lineend'))}c"
                    self.output.tag_add("prompt", match_start, match_end)
                    self.output.tag_config("prompt", foreground="#aaffaa")
                    
                    idx = match_end
        
        # Highlight errors
        if "[Error" in text or "error:" in text.lower() or "failed:" in text.lower():
            search_start_index = self.output.index(f"{start_pos} linestart")
            search_end_index = self.output.index(tk.END)
            
            error_patterns = [r"\[Error.*\]", r".*error:.*", r".*failed:.*"]
            
            idx = search_start_index
            while True:
                found_one = False
                for pattern in error_patterns:
                    match_start = self.output.search(
                        pattern, idx, stopindex=search_end_index, regexp=True, nocase=True
                    )
                    if match_start:
                        match_end = f"{match_start} lineend"
                        self.output.tag_add("error", match_start, match_end)
                        self.output.tag_config("error", foreground="#ff7777")
                        
                        idx = match_end
                        found_one = True
                        break
                
                if not found_one:
                    break
        
        # Highlight connection messages
        if "[Connected" in text or "[Disconnected" in text:
            search_start_index = self.output.index(f"{start_pos} linestart")
            search_end_index = self.output.index(tk.END)
            
            conn_patterns = [r"\[Connected.*\]", r"\[Disconnected.*\]"]
            
            idx = search_start_index
            while True:
                found_one = False
                for pattern in conn_patterns:
                    match_start = self.output.search(
                        pattern, idx, stopindex=search_end_index, regexp=True
                    )
                    if match_start:
                        match_end = f"{match_start} lineend"
                        self.output.tag_add("connection", match_start, match_end)
                        self.output.tag_config("connection", foreground="#77ccff")
                        
                        idx = match_end
                        found_one = True
                        break
                
                if not found_one:
                    break
        
        # Check for process status
        self._check_output_for_processes(text)
    
    def _check_output_for_processes(self, text):
        """Monitor output for process information"""
        if "started server process" in text.lower():
            self._check_uvicorn_status()
        
        if "llama" in text.lower() and "server listening" in text.lower():
            self._check_llama_status()
    
    def _copy_selected(self):
        """Copy selected text to clipboard"""
        try:
            selected_text = self.output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.frame.clipboard_clear()
            self.frame.clipboard_append(selected_text)
        except tk.TclError:
            pass  # No selection
    
    def _select_all(self):
        """Select all text in output"""
        self.output.tag_add(tk.SEL, "1.0", tk.END)
        self.output.mark_set(tk.INSERT, "1.0")
        self.output.see(tk.INSERT)
    
    def _clear_terminal(self):
        """Clear terminal output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete(1.0, tk.END)
        self.output.config(state=tk.NORMAL)  # Keep enabled for selection
        self.logger.log("Terminal output cleared")