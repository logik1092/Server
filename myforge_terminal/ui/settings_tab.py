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
        settings_inner = tk.Frame(self.frame, bg=self.theme_manager.bg_color, padx=10, pady=10) # Reduced padding
        settings_inner.pack(fill=tk.BOTH, expand=True)
        
        # Common padding for grid items
        self.grid_pady = (8, 8) 
        self.grid_padx = (5, 5)

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
        btn_frame.pack(pady=(20,10), fill=tk.X, anchor=tk.E) # Align to East (right)
        
        ttk.Button(btn_frame, text="Reset to Default", 
                  command=self._reset_settings, style="TButton").pack(side=tk.RIGHT, padx=(0,10))
        
        ttk.Button(btn_frame, text="Save Settings", 
                  command=self._save_settings, style="TButton").pack(side=tk.RIGHT, padx=(0,10))
    
    def _setup_connection_settings(self, parent):
        """Set up connection settings section"""
        tm = self.theme_manager
        # Use ttk.LabelFrame
        conn_frame = ttk.LabelFrame(
            parent, text="Connection Settings",
            style="TLabelFrame" # Style from MainWindow
        )
        conn_frame.pack(fill=tk.X, pady=(5,10))
        conn_frame.columnconfigure(1, weight=1) # Make entry column expandable

        # Username field
        tk.Label(conn_frame, text="Username:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=0, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Entry(conn_frame, textvariable=self.username_var, style="TEntry").grid(
            row=0, column=1, sticky=tk.EW, pady=self.grid_pady, padx=self.grid_padx)
        
        # Hostname field
        tk.Label(conn_frame, text="Hostname:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=1, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Entry(conn_frame, textvariable=self.hostname_var, style="TEntry").grid(
            row=1, column=1, sticky=tk.EW, pady=self.grid_pady, padx=self.grid_padx)
        
        # Port field
        tk.Label(conn_frame, text="Port:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=2, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Entry(conn_frame, textvariable=self.port_var, style="TEntry").grid(
            row=2, column=1, sticky=tk.EW, pady=self.grid_pady, padx=self.grid_padx)
        
        # Password field
        tk.Label(conn_frame, text="Password:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=3, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Entry(conn_frame, textvariable=self.password_var, show="*", style="TEntry").grid(
            row=3, column=1, sticky=tk.EW, pady=self.grid_pady, padx=self.grid_padx)
        
        # Checkbuttons frame for better alignment
        check_frame = tk.Frame(conn_frame, bg=tm.bg_color)
        check_frame.grid(row=4, column=1, columnspan=1, sticky=tk.W, pady=(0, self.grid_pady[1]))

        # Remember password checkbox (use ttk.Checkbutton)
        ttk.Checkbutton(
            check_frame, text="Remember password",
            variable=self.remember_var,
            style="TCheckbutton" # Style from MainWindow
        ).pack(side=tk.LEFT, anchor=tk.W, padx=(0,15))
        
        # Auto connect checkbox (use ttk.Checkbutton)
        ttk.Checkbutton(
            check_frame, text="Auto-connect on startup",
            variable=self.auto_connect_var,
            style="TCheckbutton" # Style from MainWindow
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        # SSH Key field
        tk.Label(conn_frame, text="SSH Key:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=5, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        key_frame = tk.Frame(conn_frame, bg=tm.bg_color)
        key_frame.grid(row=5, column=1, sticky=tk.EW, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Entry(key_frame, textvariable=self.key_path_var, style="TEntry").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        ttk.Button(key_frame, text="Browse", command=self._browse_key, style="TButton").pack(side=tk.RIGHT)
    
    def _setup_server_profiles(self, parent):
        """Set up server profiles section"""
        tm = self.theme_manager
        profiles_frame = ttk.LabelFrame(
            parent, text="Server Profiles",
            style="TLabelFrame"
        )
        profiles_frame.pack(fill=tk.X, pady=10)
        
        # Profiles List
        profiles_list_frame = tk.Frame(profiles_frame, bg=tm.bg_color)
        profiles_list_frame.pack(fill=tk.X, pady=(5,0), padx=5) # Added padx
        
        self.profiles_listbox = tk.Listbox(
            profiles_list_frame, height=4, # Reduced height
            bg=tm.input_bg_color, 
            fg=tm.input_fg_color,
            selectbackground=tm.accent_color_1,
            selectforeground=tm.button_fg_color, # Consistent with other selections
            borderwidth=1, # Thin border
            relief=tk.FLAT,
            highlightthickness=0, # No focus highlight
            exportselection=False
        )
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2) # Added ipady
        
        # Scrollbar
        profiles_scrollbar = ttk.Scrollbar( # Use ttk.Scrollbar
            profiles_list_frame, orient=tk.VERTICAL,
            command=self.profiles_listbox.yview, style="TScrollbar"
        )
        profiles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_listbox.config(yscrollcommand=profiles_scrollbar.set)
        
        # Populate profiles
        self._populate_profiles()
        
        # Bind selection
        self.profiles_listbox.bind('<<ListboxSelect>>', self._on_profile_selected)
        
        # Buttons
        profiles_btn_frame = tk.Frame(profiles_frame, bg=tm.bg_color)
        profiles_btn_frame.pack(fill=tk.X, pady=(5,8), padx=5) # Adjusted padding
        
        button_padx = (0,10)
        ttk.Button(profiles_btn_frame, text="Add Current", 
                  command=self._add_profile, style="TButton").pack(side=tk.LEFT, padx=button_padx)
        
        ttk.Button(profiles_btn_frame, text="Update Selected", 
                  command=self._update_profile, style="TButton").pack(side=tk.LEFT, padx=button_padx)
        
        ttk.Button(profiles_btn_frame, text="Remove Selected", 
                  command=self._remove_profile, style="TButton").pack(side=tk.LEFT, padx=(button_padx[0], 0))
    
    def _setup_ui_settings(self, parent):
        """Set up UI settings section"""
        tm = self.theme_manager
        ui_frame = ttk.LabelFrame(
            parent, text="Interface Settings",
            style="TLabelFrame"
        )
        ui_frame.pack(fill=tk.X, pady=10)
        ui_frame.columnconfigure(1, weight=1) # Make control column expandable
        
        # Font size
        tk.Label(ui_frame, text="Font Size:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=0, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        font_frame = tk.Frame(ui_frame, bg=tm.bg_color)
        font_frame.grid(row=0, column=1, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        ttk.Button(font_frame, text="-", width=3, style="TButton",
                  command=lambda: self._change_font_size(-1)).pack(side=tk.LEFT)
        
        tk.Label(font_frame, textvariable=self.font_size_var, width=4, anchor=tk.CENTER,
                bg=tm.input_bg_color, fg=tm.input_fg_color).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(font_frame, text="+", width=3, style="TButton",
                  command=lambda: self._change_font_size(1)).pack(side=tk.LEFT)
        
        # Theme selection
        tk.Label(ui_frame, text="Theme:", 
                bg=tm.bg_color, fg=tm.fg_color).grid(
            row=1, column=0, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        theme_frame = tk.Frame(ui_frame, bg=tm.bg_color)
        theme_frame.grid(row=1, column=1, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
        
        # Use ttk.Radiobutton
        ttk.Radiobutton(
            theme_frame, text="Dark", variable=self.theme_var, value="dark",
            style="TRadiobutton" # Style from MainWindow
        ).pack(side=tk.LEFT, padx=(0,5))
        
        ttk.Radiobutton(
            theme_frame, text="Light", variable=self.theme_var, value="light",
            style="TRadiobutton" # Style from MainWindow
        ).pack(side=tk.LEFT, padx=(0,5))
        
        # Log commands checkbox (use ttk.Checkbutton)
        ttk.Checkbutton(
            ui_frame, text="Log commands and responses",
            variable=self.log_commands_var,
            style="TCheckbutton" # Style from MainWindow
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=self.grid_pady, padx=self.grid_padx)
    
    def _setup_commands_settings(self, parent):
        """Set up commands settings section"""
        tm = self.theme_manager
        commands_frame = ttk.LabelFrame(
            parent, text="Custom Commands", # Renamed for clarity
            style="TLabelFrame"
        )
        commands_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(commands_frame, text="Edit Custom Commands", style="TButton",
                  command=self._edit_commands).pack(pady=10, padx=10, anchor=tk.W) # Added padding and anchor
    
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