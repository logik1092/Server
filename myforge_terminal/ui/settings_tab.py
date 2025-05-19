"""
File: myforge_terminal/ui/settings_tab.py
Description: Settings Tab Module - Application configuration settings

Structure:
  Classes:
    SettingsTab:
      Description: Initialize settings tab
      - __init__(self, notebook, config, logger, theme_manager)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class SettingsTab:
    def __init__(self, notebook, config, logger, theme_manager):
        """Initialize settings tab"""
        self.notebook = notebook
        self.config = config
        self.logger = logger
        self.theme_manager = theme_manager
        
        # Create frame for settings tab
        self.frame = tk.Frame(notebook, bg=theme_manager.bg_color)
        
        # Setup variables
        self._setup_variables()
        
        # Setup UI
        self._setup_ui()
    
    def _setup_variables(self):
        """Set up variables for settings"""
        # Connection settings
        self.username_var = tk.StringVar(value=self.config.get("username", "forgeadmin"))
        self.hostname_var = tk.StringVar(value=self.config.get("hostname", "209.145.57.9"))
        self.port_var = tk.StringVar(value=str(self.config.get("port", 22)))
        self.password_var = tk.StringVar(value=self.config.get("password", ""))
        self.remember_var = tk.BooleanVar(value=bool(self.config.get("password", "")))
        self.key_path_var = tk.StringVar(value=self.config.get("key_path", ""))
        
        # Interface settings
        self.font_size_var = tk.IntVar(value=self.config.get("font_size", 10))
        self.theme_var = tk.StringVar(value=self.config.get("theme", "dark"))
        self.log_commands_var = tk.BooleanVar(value=self.config.get("log_commands", True))
        self.auto_connect_var = tk.BooleanVar(value=self.config.get("auto_connect", False))
    
    def _setup_ui(self):
        """Set up settings tab UI"""
        settings_inner = tk.Frame(self.frame, bg=self.theme_manager.bg_color, padx=20, pady=20)
        settings_inner.pack(fill=tk.BOTH, expand=True)
        
        # Connection settings
        self._setup_connection_settings(settings_inner)
        
        # Server profiles
        self._setup_server_profiles(settings_inner)
        
        # UI settings
        self._setup_ui_settings(settings_inner)
        
        # Commands settings
        self._setup_commands_settings(settings_inner)
        
        # Buttons
        btn_frame = tk.Frame(settings_inner, bg=self.theme_manager.bg_color)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Save Settings", 
                  command=self._save_settings).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="Reset to Default", 
                  command=self._reset_settings).pack(side=tk.LEFT, padx=10)
    
    def _setup_connection_settings(self, parent):
        """Set up connection settings section"""
        conn_frame = tk.LabelFrame(
            parent, text="Connection Settings",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            padx=10, pady=10
        )
        conn_frame.pack(fill=tk.X, pady=10)
        
        # Username field
        tk.Label(conn_frame, text="Username:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        tk.Entry(conn_frame, textvariable=self.username_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color).grid(
            row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Hostname field
        tk.Label(conn_frame, text="Hostname:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        tk.Entry(conn_frame, textvariable=self.hostname_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color).grid(
            row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Port field
        tk.Label(conn_frame, text="Port:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        tk.Entry(conn_frame, textvariable=self.port_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color).grid(
            row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Password field
        tk.Label(conn_frame, text="Password:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        tk.Entry(conn_frame, textvariable=self.password_var, show="*", 
                bg="#2d2d2d", fg=self.theme_manager.fg_color).grid(
            row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Remember password checkbox
        tk.Checkbutton(
            conn_frame, text="Remember password",
            variable=self.remember_var,
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Auto connect checkbox
        tk.Checkbutton(
            conn_frame, text="Auto-connect on startup",
            variable=self.auto_connect_var,
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # SSH Key field
        tk.Label(conn_frame, text="SSH Key:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=6, column=0, sticky=tk.W, pady=5)
        
        key_frame = tk.Frame(conn_frame, bg=self.theme_manager.bg_color)
        key_frame.grid(row=6, column=1, sticky=tk.W+tk.E, pady=5)
        
        tk.Entry(key_frame, textvariable=self.key_path_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(key_frame, text="Browse", 
                  command=self._browse_key).pack(side=tk.RIGHT, padx=5)
    
    def _setup_server_profiles(self, parent):
        """Set up server profiles section"""
        profiles_frame = tk.LabelFrame(
            parent, text="Server Profiles",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            padx=10, pady=10
        )
        profiles_frame.pack(fill=tk.X, pady=10)
        
        # Profiles List
        profiles_list_frame = tk.Frame(profiles_frame, bg=self.theme_manager.bg_color)
        profiles_list_frame.pack(fill=tk.X, pady=5)
        
        self.profiles_listbox = tk.Listbox(
            profiles_list_frame, height=5,
            bg="#2d2d2d", fg=self.theme_manager.fg_color,
            selectbackground=self.theme_manager.accent_color,
            selectforeground="#ffffff"
        )
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar
        profiles_scrollbar = ttk.Scrollbar(
            profiles_list_frame, orient=tk.VERTICAL,
            command=self.profiles_listbox.yview
        )
        profiles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_listbox.config(yscrollcommand=profiles_scrollbar.set)
        
        # Populate profiles
        self._populate_profiles()
        
        # Bind selection
        self.profiles_listbox.bind('<<ListboxSelect>>', self._on_profile_selected)
        
        # Buttons
        profiles_btn_frame = tk.Frame(profiles_frame, bg=self.theme_manager.bg_color)
        profiles_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(profiles_btn_frame, text="Add Current", 
                  command=self._add_profile).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(profiles_btn_frame, text="Update Selected", 
                  command=self._update_profile).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(profiles_btn_frame, text="Remove Selected", 
                  command=self._remove_profile).pack(side=tk.LEFT, padx=5)
    
    def _setup_ui_settings(self, parent):
        """Set up UI settings section"""
        ui_frame = tk.LabelFrame(
            parent, text="Interface Settings",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            padx=10, pady=10
        )
        ui_frame.pack(fill=tk.X, pady=10)
        
        # Font size
        tk.Label(ui_frame, text="Font Size:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        font_frame = tk.Frame(ui_frame, bg=self.theme_manager.bg_color)
        font_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Button(font_frame, text="-", width=3, 
                  command=lambda: self._change_font_size(-1)).pack(side=tk.LEFT)
        
        tk.Label(font_frame, textvariable=self.font_size_var, width=3, 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(font_frame, text="+", width=3, 
                  command=lambda: self._change_font_size(1)).pack(side=tk.LEFT)
        
        # Theme selection
        tk.Label(ui_frame, text="Theme:", 
                bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        theme_frame = tk.Frame(ui_frame, bg=self.theme_manager.bg_color)
        theme_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Radiobutton(
            theme_frame, text="Dark", variable=self.theme_var, value="dark",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).pack(side=tk.LEFT)
        
        tk.Radiobutton(
            theme_frame, text="Light", variable=self.theme_var, value="light",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).pack(side=tk.LEFT, padx=10)
        
        # Log commands checkbox
        tk.Checkbutton(
            ui_frame, text="Log commands and responses",
            variable=self.log_commands_var,
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            selectcolor="#2d2d2d",
            activebackground=self.theme_manager.bg_color,
            activeforeground=self.theme_manager.fg_color
        ).grid(row=2, column=1, sticky=tk.W, pady=5)
    
    def _setup_commands_settings(self, parent):
        """Set up commands settings section"""
        commands_frame = tk.LabelFrame(
            parent, text="Commands",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            padx=10, pady=10
        )
        commands_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(commands_frame, text="Edit Custom Commands", 
                  command=self._edit_commands).pack(pady=5)
    
    def _populate_profiles(self):
        """Populate server profiles listbox"""
        self.profiles_listbox.delete(0, tk.END)
        
        servers = self.config.get("servers", {})
        for name, info in servers.items():
            self.profiles_listbox.insert(tk.END, f"{name} ({info['username']}@{info['hostname']}:{info['port']})")
    
    def _on_profile_selected(self, event):
        """Handle profile selection"""
        selection = self.profiles_listbox.curselection()
        if not selection:
            return
        
        # Get selected profile
        profile_text = self.profiles_listbox.get(selection[0])
        profile_name = profile_text.split(" (")[0]
        
        # Get profile info
        servers = self.config.get("servers", {})
        if profile_name in servers:
            info = servers[profile_name]
            
            # Update fields
            self.username_var.set(info.get("username", ""))
            self.hostname_var.set(info.get("hostname", ""))
            self.port_var.set(str(info.get("port", 22)))
    
    def _add_profile(self):
        """Add current settings as a profile"""
        from tkinter import simpledialog
        
        # Get profile name
        profile_name = simpledialog.askstring(
            "Profile Name",
            "Enter a name for this server profile:",
            parent=self.frame
        )
        
        if not profile_name:
            return
        
        # Create profile
        servers = self.config.get("servers", {})
        servers[profile_name] = {
            "username": self.username_var.get(),
            "hostname": self.hostname_var.get(),
            "port": int(self.port_var.get()) if self.port_var.get().isdigit() else 22
        }
        
        # Update config
        self.config.set("servers", servers)
        
        # Update listbox
        self._populate_profiles()
        
        # Log
        self.logger.log(f"Added server profile: {profile_name}")
        
        # Show confirmation
        messagebox.showinfo(
            "Profile Added",
            f"Server profile '{profile_name}' has been added."
        )
    
    def _update_profile(self):
        """Update selected profile with current settings"""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "No Selection",
                "Please select a profile to update."
            )
            return
        
        # Get selected profile
        profile_text = self.profiles_listbox.get(selection[0])
        profile_name = profile_text.split(" (")[0]
        
        # Confirm update
        if not messagebox.askyesno(
            "Confirm Update",
            f"Update profile '{profile_name}' with current settings?"
        ):
            return
        
        # Update profile
        servers = self.config.get("servers", {})
        if profile_name in servers:
            servers[profile_name] = {
                "username": self.username_var.get(),
                "hostname": self.hostname_var.get(),
                "port": int(self.port_var.get()) if self.port_var.get().isdigit() else 22
            }
            
            # Update config
            self.config.set("servers", servers)
            
            # Update listbox
            self._populate_profiles()
            
            # Log
            self.logger.log(f"Updated server profile: {profile_name}")
            
            # Show confirmation
            messagebox.showinfo(
                "Profile Updated",
                f"Server profile '{profile_name}' has been updated."
            )
    
    def _remove_profile(self):
        """Remove selected profile"""
        selection = self.profiles_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "No Selection",
                "Please select a profile to remove."
            )
            return
        
        # Get selected profile
        profile_text = self.profiles_listbox.get(selection[0])
        profile_name = profile_text.split(" (")[0]
        
        # Confirm removal
        if not messagebox.askyesno(
            "Confirm Removal",
            f"Remove profile '{profile_name}'?"
        ):
            return
        
        # Remove profile
        servers = self.config.get("servers", {})
        if profile_name in servers:
            del servers[profile_name]
            
            # Update config
            self.config.set("servers", servers)
            
            # Update listbox
            self._populate_profiles()
            
            # Log
            self.logger.log(f"Removed server profile: {profile_name}")
            
            # Show confirmation
            messagebox.showinfo(
                "Profile Removed",
                f"Server profile '{profile_name}' has been removed."
            )
    
    def _browse_key(self):
        """Browse for SSH key file"""
        filename = filedialog.askopenfilename(
            title="Select SSH Key File",
            filetypes=(
                ("All Files", "*.*"),
                ("PEM Files", "*.pem"),
                ("PPK Files", "*.ppk")
            )
        )
        
        if filename:
            self.key_path_var.set(filename)
    
    def _change_font_size(self, delta):
        """Change font size by delta"""
        new_size = self.font_size_var.get() + delta
        if 6 <= new_size <= 18:
            self.font_size_var.set(new_size)
    
    def _edit_commands(self):
        """Edit custom commands"""
        from ui.dialogs import CommandEditorDialog
        
        CommandEditorDialog(
            self.frame,
            self.config,
            self.logger,
            self.theme_manager
        )
    
    def _save_settings(self):
        """Save current settings"""
        # Update settings from UI
        self.config.set("username", self.username_var.get())
        self.config.set("hostname", self.hostname_var.get())
        self.config.set("port", int(self.port_var.get()) if self.port_var.get().isdigit() else 22)
        
        # Password handling
        if self.remember_var.get():
            self.config.set("password", self.password_var.get())
        else:
            self.config.set("password", "")
        
        # SSH key path
        self.config.set("key_path", self.key_path_var.get())
        
        # UI settings
        self.config.set("font_size", self.font_size_var.get())
        self.config.set("theme", self.theme_var.get())
        self.config.set("log_commands", self.log_commands_var.get())
        self.config.set("auto_connect", self.auto_connect_var.get())
        
        # Save to file
        self.config.save()
        
        # Apply theme
        self.theme_manager.apply_theme(self.theme_var.get())
        
        # Log
        self.logger.log("Settings saved")
        
        # Show confirmation
        messagebox.showinfo(
            "Settings Saved",
            "Settings have been saved successfully."
        )
    
    def _reset_settings(self):
        """Reset settings to default"""
        if not messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all settings to default?"
        ):
            return
        
        # Default settings
        self.config.reset_to_default()
        
        # Update UI with defaults
        self._setup_variables()
        
        # Update listbox
        self._populate_profiles()
        
        # Apply theme
        self.theme_manager.apply_theme(self.theme_var.get())
        
        # Log
        self.logger.log("Settings reset to default")
        
        # Show confirmation
        messagebox.showinfo(
            "Settings Reset",
            "Settings have been reset to default."
        )