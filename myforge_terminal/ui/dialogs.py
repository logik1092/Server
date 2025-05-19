"""
File: myforge_terminal/ui/dialogs.py
Description: Dialog Module - Custom dialogs for specific functionality

Structure:
  Classes:
    CheatSheetDialog:
      Description: Dialog showing SSH command cheat sheet
      - __init__(self, parent, config, theme_manager, inject_command=None)
    CommandEditorDialog:
      Description: Dialog for editing custom commands
      - __init__(self, parent, config, logger, theme_manager)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os

class CheatSheetDialog:
    """Dialog showing SSH command cheat sheet"""
    
    def __init__(self, parent, config, theme_manager, inject_command=None):
        """Initialize cheat sheet dialog"""
        self.parent = parent
        self.config = config
        self.theme_manager = theme_manager
        self.inject_command = inject_command
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("SSH Command Cheat Sheet")
        self.dialog.geometry("800x700")
        self.dialog.configure(bg=theme_manager.bg_color)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_window()
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up dialog UI"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Define categories
        categories = {
            "Server Connection": [
                ("Connect to Servers", [
                    "ssh root@149.28.126.226      # VULTR",
                    "ssh -v forgeadmin@209.145.57.9"
                ]),
                ("Basic Tips", [
                    "`Tab` key → auto-completes filenames/directories.",
                    "`Ctrl+C` → cancel current running command.",
                    "`Ctrl+X` → exit Nano editor.",
                    "`Ctrl+O` → save file in Nano.",
                    "`Up Arrow` → show your last command again."
                ])
            ],
            "Application Commands": [
                ("Virtual Environment", [
                    "source /var/www/myforge.ai/venv/bin/activate"
                ]),
                ("Launch Applications", [
                    "uvicorn server:app --host 0.0.0.0 --port=8080 --reload",
                    "cd /var/www/myforge.ai/llama.cpp/build/bin",
                    "./llama-server -m ../../models/openchat-3.5-0106.Q4_K_M.gguf --port 8001 --threads 6"
                ]),
                ("Control Applications", [
                    "sudo systemctl reload nginx",
                    "pkill -f uvicorn"
                ])
            ],
            "Navigation & Files": [
                ("Navigate Folders", [
                    "cd /path/to/folder         # Change directory",
                    "cd /var/www/myforge.ai      # (Your website files)",
                    "cd /etc/nginx/sites-available  # (Nginx config files)",
                    "cd ~                        # Go back to home directory"
                ]),
                ("List Files", [
                    "ls                         # List files",
                    "ls -l                      # Detailed list (permissions, size, date)"
                ]),
                ("Create / Edit Files", [
                    "nano filename.ext          # Open/create file in Nano editor",
                    "nano index.html            # Edit index.html"
                ]),
                ("Delete Files", [
                    "rm filename.ext            # Delete file",
                    "rm index.html              # Delete old index.html"
                ]),
                ("Upload Files", [
                    "scp \"C:\\path\\to\\file.ext\" root@149.28.126.226:/path/on/server/",
                    "scp \"C:\\1bible\\mod\\new_index.html\" root@149.28.126.226:/var/www/myforge.ai/index.html"
                ])
            ],
            "Services & Processes": [
                ("Nginx Management", [
                    "systemctl reload nginx      # Reload Nginx after config changes",
                    "systemctl restart nginx     # Full Nginx restart",
                    "systemctl status nginx      # See if Nginx is running",
                    "nginx -t                    # Test Nginx configuration"
                ]),
                ("Background Processes", [
                    "nohup python3 server.py --port 42181 &",
                    "nohup python3 yourscript.py &",
                    "# `nohup` makes it survive even if you close the SSH session.",
                    "# `&` runs it in the background."
                ]),
                ("Process Management", [
                    "ps aux | grep python        # View running Python processes",
                    "kill PID                    # Kill a process (replace PID with process ID)"
                ]),
                ("Health Check", [
                    "curl http://localhost:42181/health  # Check if local API is healthy"
                ])
            ]
        }
        
        # Create tabs for each category
        for category, sections in categories.items():
            tab = tk.Frame(notebook, bg=self.theme_manager.bg_color, padx=10, pady=10)
            notebook.add(tab, text=category)
            
            # Add scrollable canvas
            canvas = tk.Canvas(tab, bg=self.theme_manager.bg_color, highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            
            scrollable_frame = tk.Frame(canvas, bg=self.theme_manager.bg_color)
            scrollable_frame.bind(
                "<Configure>",
                lambda e, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add sections
            row = 0
            for section_title, commands in sections:
                section_label = tk.Label(
                    scrollable_frame, text=section_title,
                    font=("Arial", 12, "bold"),
                    bg=self.theme_manager.bg_color, fg=self.theme_manager.accent_color,
                    anchor=tk.W
                )
                section_label.grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
                row += 1
                
                # Add commands
                for command in commands:
                    cmd_frame = tk.Frame(scrollable_frame, bg=self.theme_manager.bg_color)
                    cmd_frame.grid(row=row, column=0, sticky=tk.W+tk.E, pady=2)
                    
                    cmd_text = tk.Label(
                        cmd_frame, text=command,
                        font=("Consolas", 10),
                        bg="#2d2d2d", fg="#aaffaa",
                        anchor=tk.W, padx=5, pady=3,
                        wraplength=600, justify=tk.LEFT
                    )
                    cmd_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    
                    copy_btn = ttk.Button(
                        cmd_frame, text="Copy", width=6,
                        command=lambda cmd=command: self._copy_to_clipboard(cmd)
                    )
                    copy_btn.pack(side=tk.RIGHT, padx=5)
                    
                    # Add Run button for non-comment commands
                    if not command.strip().startswith('#') and not command.startswith('`'):
                        run_btn = ttk.Button(
                            cmd_frame, text="Run", width=6,
                            command=lambda cmd=command: self._run_command(cmd)
                        )
                        run_btn.pack(side=tk.RIGHT, padx=0)
                    
                    row += 1
                
                # Add separator
                separator = ttk.Separator(scrollable_frame, orient="horizontal")
                separator.grid(row=row, column=0, sticky=tk.W+tk.E, pady=5)
                row += 1
        
        # Button frame
        btn_frame = tk.Frame(self.dialog, bg=self.theme_manager.bg_color)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="Export to File",
            command=self._export_cheat_sheet
        ).pack(side=tk.LEFT, padx=5)
    
    def _copy_to_clipboard(self, text):
        """Copy command to clipboard"""
        # Extract command part (before comment)
        if '#' in text:
            command_part = text.split('#')[0].strip()
        else:
            command_part = text.strip()
        
        # Copy to clipboard
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(command_part)
        
        # Show status message (optional)
        messagebox.showinfo("Copied", "Command copied to clipboard.", parent=self.dialog)
    
    def _run_command(self, command):
        """Run command in terminal"""
        # Extract command part (before comment)
        if '#' in command:
            command_part = command.split('#')[0].strip()
        else:
            command_part = command.strip()
        
        # Check for local SCP command
        if command_part.startswith('scp '):
            messagebox.showinfo(
                "Local Command",
                "This is a local command meant to be run on your PC, not on the server.",
                parent=self.dialog
            )
            return
        
        # Close dialog
        self.dialog.destroy()
        
        # Run command in terminal
        if self.inject_command:
            self.inject_command(command_part)
    
    def _export_cheat_sheet(self):
        """Export cheat sheet to a file"""
        filename = filedialog.asksaveasfilename(
            title="Export Cheat Sheet",
            defaultextension=".md",
            filetypes=(
                ("Markdown Files", "*.md"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ),
            parent=self.dialog
        )
        
        if not filename:
            return
        
        try:
            with open(filename, "w") as f:
                f.write("# 🛠 Common Server Commands (Cheat Sheet)\n\n")
                
                # Define categories for export
                categories = {
                    "Connect to Server": [
                        "ssh root@149.28.126.226      # VULTR",
                        "ssh -v forgeadmin@209.145.57.9"
                    ],
                    "VIRTUAL ENV": [
                        "source /var/www/myforge.ai/venv/bin/activate",
                        "uvicorn server:app --host 0.0.0.0 --port=8080 --reload"
                    ],
                    "LAUNCH AI": [
                        "cd /var/www/myforge.ai/llama.cpp/build/bin",
                        "./llama-server -m ../../models/openchat-3.5-0106.Q4_K_M.gguf --port 8001 --threads 6",
                        "sudo systemctl reload nginx",
                        "pkill -f uvicorn"
                    ],
                    "Navigate Folders": [
                        "cd /path/to/folder         # Change directory",
                        "cd /var/www/myforge.ai      # (Your website files)",
                        "cd /etc/nginx/sites-available  # (Nginx config files)",
                        "cd ~                        # Go back to home directory"
                    ],
                    "List Files": [
                        "ls                         # List files",
                        "ls -l                      # Detailed list (permissions, size, date)"
                    ],
                    "Create / Edit Files": [
                        "nano filename.ext          # Open/create file in Nano editor",
                        "nano index.html            # Edit index.html"
                    ],
                    "Delete Files": [
                        "rm filename.ext            # Delete file",
                        "rm index.html              # Delete old index.html"
                    ],
                    "Upload Files From PC to Server (via SCP)": [
                        "scp \"C:\\path\\to\\file.ext\" root@149.28.126.226:/path/on/server/",
                        "Example:",
                        "scp \"C:\\1bible\\mod\\new_index.html\" root@149.28.126.226:/var/www/myforge.ai/index.html"
                    ],
                    "Restart/Reload Services": [
                        "systemctl reload nginx      # Reload Nginx after config changes",
                        "systemctl restart nginx     # Full Nginx restart",
                        "systemctl status nginx      # See if Nginx is running"
                    ],
                    "Test Nginx Configuration": [
                        "nginx -t"
                    ],
                    "Run Python Scripts (in background)": [
                        "nohup python3 server.py --port 42181 &",
                        "nohup python3 yourscript.py &",
                        "- `nohup` makes it survive even if you close the SSH session.",
                        "- `&` runs it in the background."
                    ],
                    "View Running Processes": [
                        "ps aux | grep python"
                    ],
                    "Kill a Process (if needed)": [
                        "kill PID",
                        "(Replace `PID` with the process ID you find from `ps aux | grep python`.)"
                    ],
                    "Basic Health Check": [
                        "curl http://localhost:42181/health",
                        "(Check if your local GPU API is still healthy.)"
                    ],
                    "Tips": [
                        "`Tab` key → auto-completes filenames/directories.",
                        "`Ctrl+C` → cancel current running command.",
                        "`Ctrl+X` → exit Nano editor.",
                        "`Ctrl+O` → save file in Nano.",
                        "`Up Arrow` → show your last command again."
                    ]
                }
                
                # Write categories
                for category, commands in categories.items():
                    f.write(f"## 🔹 {category}\n```bash\n")
                    for cmd in commands:
                        f.write(f"{cmd}\n")
                    f.write("```\n\n")
            
            messagebox.showinfo(
                "Export Complete",
                f"Cheat sheet exported to {filename}",
                parent=self.dialog
            )
        
        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Error exporting cheat sheet: {e}",
                parent=self.dialog
            )
    
    def _center_window(self):
        """Center dialog on parent"""
        self.dialog.withdraw()
        self.dialog.update_idletasks()
        
        # Calculate position x, y
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
        self.dialog.deiconify()

class CommandEditorDialog:
    """Dialog for editing custom commands"""
    
    def __init__(self, parent, config, logger, theme_manager):
        """Initialize command editor dialog"""
        self.parent = parent
        self.config = config
        self.logger = logger
        self.theme_manager = theme_manager
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Custom Commands")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg=theme_manager.bg_color)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_window()
        
        # Setup variables
        self.cmd_entries = {}  # Store Entry widgets
        self.current_row = 0   # Track current row for layout
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up dialog UI"""
        # Header
        tk.Label(
            self.dialog, text="Edit Custom Commands",
            font=("Arial", 12, "bold"),
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
        ).pack(pady=10)
        
        # Main scrollable frame
        main_frame = tk.Frame(self.dialog, bg=self.theme_manager.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame, bg=self.theme_manager.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=self.theme_manager.bg_color)
        scrollable_frame.bind(
            "<Configure>",
            lambda e, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Function to add command field
        def add_command_field(name, value):
            cmd_frame = tk.Frame(scrollable_frame, bg=self.theme_manager.bg_color)
            cmd_frame.grid(row=self.current_row, column=0, sticky=tk.EW, pady=2)
            self.current_row += 1
            
            # Ensure frame expands
            scrollable_frame.columnconfigure(0, weight=1)
            
            # Format display name
            display_name = name.replace('_', ' ').title()
            
            # Label
            tk.Label(
                cmd_frame, text=f"{display_name}:",
                width=20, anchor=tk.W,
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
            ).pack(side=tk.LEFT, padx=5)
            
            # Entry
            entry = tk.Entry(
                cmd_frame,
                bg="#2d2d2d", fg=self.theme_manager.fg_color,
                insertbackground=self.theme_manager.fg_color
            )
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Store entry
            self.cmd_entries[name] = entry
            
            # Delete button
            del_btn = ttk.Button(
                cmd_frame, text="X", width=3,
                command=lambda n=name, f=cmd_frame: self._delete_command(n, f)
            )
            del_btn.pack(side=tk.RIGHT, padx=5)
        
        # Add fields for existing commands
        commands = self.config.get("commands", {})
        for cmd_name, cmd_value in commands.items():
            add_command_field(cmd_name, cmd_value)
        
        # Add new command button
        add_btn_frame = tk.Frame(scrollable_frame, bg=self.theme_manager.bg_color)
        add_btn_frame.grid(row=self.current_row, column=0, pady=10, sticky=tk.W)
        
        ttk.Button(
            add_btn_frame, text="Add New Command",
            command=lambda: self._add_new_command(add_command_field)
        ).pack(side=tk.LEFT)
        
        # Button frame
        btn_frame = tk.Frame(self.dialog, bg=self.theme_manager.bg_color)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, text="Save",
            command=self._save_commands
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame, text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=10)
    
    def _delete_command(self, name, frame):
        """Delete a command"""
        if name in self.cmd_entries:
            del self.cmd_entries[name]
        
        frame.destroy()
    
    def _add_new_command(self, add_field_callback):
        """Add a new command"""
        cmd_name = simpledialog.askstring(
            "New Command Name",
            "Enter a short, unique name for the command (e.g., 'my_script'):",
            parent=self.dialog
        )
        
        if not cmd_name:
            return
        
        # Format command name
        cmd_name = cmd_name.lower().replace(' ', '_').strip()
        
        if not cmd_name:
            messagebox.showerror(
                "Invalid Name",
                "Command name cannot be empty.",
                parent=self.dialog
            )
            return
        
        # Check if command name already exists
        if cmd_name in self.cmd_entries:
            messagebox.showerror(
                "Duplicate Name",
                f"Command '{cmd_name}' already exists.",
                parent=self.dialog
            )
            return
        
        # Get command value
        cmd_value = simpledialog.askstring(
            "New Command Value",
            f"Enter the command to run for '{cmd_name}':",
            parent=self.dialog
        )
        
        if cmd_value is None:
            return
        
        # Add field
        add_field_callback(cmd_name, cmd_value)
    
    def _save_commands(self):
        """Save commands"""
        # Collect commands from entries
        new_commands = {}
        
        for cmd_name, entry in self.cmd_entries.items():
            if entry.winfo_exists():  # Check if widget still exists
                new_commands[cmd_name] = entry.get()
        
        # Update config
        self.config.set("commands", new_commands)
        self.config.save()
        
        # Log
        self.logger.log("Custom commands updated")
        
        # Close dialog
        self.dialog.destroy()
        
        # Show confirmation
        messagebox.showinfo(
            "Commands Saved",
            "Custom commands have been saved. Restart app or terminal tab for changes to take effect."
        )
    
    def _center_window(self):
        """Center dialog on parent"""
        self.dialog.withdraw()
        self.dialog.update_idletasks()
        
        # Calculate position x, y
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
        self.dialog.deiconify()