"""
File: myforge_terminal/ui/main_window.py
Description: Main Window Module - Main application window and notebook tabs

Structure:
  Classes:
    MainWindow:
      Description: Initialize main application window
      - __init__(self, root, config, logger)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from ssh.client import SSHClient
from ssh.sftp import SFTPOperations
from ui.terminal_tab import TerminalTab
from ui.file_explorer_tab import FileExplorerTab
from ui.settings_tab import SettingsTab
from ui.logs_tab import LogsTab
from utils.ui_utils import ThemeManager

class MainWindow:
    def __init__(self, root, config, logger):
        """Initialize main application window"""
        self.root = root
        self.config = config
        self.logger = logger
        
        # Set window properties
        self.root.title("MyForge SSH Terminal")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize components
        self.ssh_client = SSHClient(config, logger)
        self.sftp_ops = SFTPOperations(self.ssh_client, logger)
        
        # Set up theme manager
        self.theme_manager = ThemeManager(self.root, config)
        self.theme_manager.apply_theme(config.get("theme", "dark"))
        self._apply_custom_styles() # Apply custom styles after base theme
        
        # Create main frame
        self.main_frame = tk.Frame(root, bg=self.theme_manager.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Set up window layout
        self._setup_layout()
        
        # Set up event bindings
        self._setup_bindings()
        
        # Auto-connect if configured
        if config.get("auto_connect", False) and config.get("password", ""):
            self.root.after(1000, self._auto_connect)
    
    def _setup_layout(self):
        """Set up main window layout"""
        # Server selection frame
        self.server_frame = tk.Frame(self.main_frame, bg=self.theme_manager.bg_color)
        self.server_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Server selection dropdown
        tk.Label(self.server_frame, text="Server:", 
                 bg=self.theme_manager.bg_color, 
                 fg=self.theme_manager.fg_color).pack(side=tk.LEFT, padx=(0, 5)) # Adjusted padx
        
        # Get server options
        servers = self.config.get("servers", {})
        server_options = [f"{name} ({info['username']}@{info['hostname']})" 
                          for name, info in servers.items()]
        
        self.server_var = tk.StringVar()
        self.server_dropdown = ttk.Combobox(self.server_frame, 
                                           textvariable=self.server_var, 
                                           values=server_options,
                                           style="TCombobox") # Apply style
        self.server_dropdown.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True) # Adjusted padx
        
        if server_options:
            self.server_dropdown.current(0)
        
        # Connect button
        self.connect_btn = ttk.Button(self.server_frame, text="Connect", 
                                     command=self._connect_selected,
                                     style="TButton") # Apply style
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5)) # Adjusted padx
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(self.server_frame, text="Disconnect", 
                                        command=self._disconnect,
                                        state=tk.DISABLED,
                                        style="TButton") # Apply style
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 0)) # Adjusted padx
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame, style="TNotebook") # Apply style
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,10)) # Adjusted pady
        
        # Create tabs
        self.terminal_tab = TerminalTab(self.notebook, self.ssh_client, 
                                       self.config, self.logger, self.theme_manager)
        self.notebook.add(self.terminal_tab.frame, text="Terminal")
        
        self.file_explorer_tab = FileExplorerTab(self.notebook, self.ssh_client, 
                                               self.sftp_ops, self.config, 
                                               self.logger, self.theme_manager)
        self.notebook.add(self.file_explorer_tab.frame, text="File Explorer")
        
        self.settings_tab = SettingsTab(self.notebook, self.config, 
                                       self.logger, self.theme_manager)
        self.notebook.add(self.settings_tab.frame, text="Settings")
        
        self.logs_tab = LogsTab(self.notebook, self.logger, self.theme_manager)
        self.notebook.add(self.logs_tab.frame, text="Logs")
        
        # System monitor frame
        # Use ThemeManager color for monitor_frame background
        self.monitor_frame = tk.Frame(self.main_frame, bg=self.theme_manager.bg_color, height=28) 
        self.monitor_frame.pack(fill=tk.X, padx=10, pady=(0, 0)) # Adjusted pady
        self.monitor_frame.pack_propagate(False) # Prevent resizing
        
        # Status variables
        self.server_name_var = tk.StringVar(value="SERVER: Not connected")
        self.cpu_var = tk.StringVar(value="CPU: --")
        self.mem_var = tk.StringVar(value="MEM: --")
        self.disk_var = tk.StringVar(value="DISK: --")
        
        # Status labels
        tm = self.theme_manager # Shorthand for ThemeManager
        monitor_font = ('Segoe UI', 8) # Smaller font for monitor bar

        tk.Label(self.monitor_frame, textvariable=self.server_name_var, 
                bg=tm.bg_color, fg=tm.accent_color_1, padx=10, font=monitor_font).pack(side=tk.LEFT, pady=2)
        tk.Label(self.monitor_frame, textvariable=self.cpu_var, 
                bg=tm.bg_color, fg=tm.fg_color, padx=10, font=monitor_font).pack(side=tk.LEFT, pady=2)
        tk.Label(self.monitor_frame, textvariable=self.mem_var, 
                bg=tm.bg_color, fg=tm.fg_color, padx=10, font=monitor_font).pack(side=tk.LEFT, pady=2)
        tk.Label(self.monitor_frame, textvariable=self.disk_var, 
                bg=tm.bg_color, fg=tm.fg_color, padx=10, font=monitor_font).pack(side=tk.LEFT, pady=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_bar = tk.Label(self.main_frame, textvariable=self.status_var, 
                                  bd=0, relief=tk.FLAT, anchor=tk.W, # Modernized relief
                                  bg=tm.accent_color_1, fg=tm.button_fg_color, # Styled like a banner
                                  padx=10, pady=4) # Added padding
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0) # Fill full width, no external X padding
        
        # Set up callbacks
        self._setup_callbacks()

    def _apply_custom_styles(self):
        """Apply custom ttk styles for a modern look, integrated with ThemeManager."""
        style = ttk.Style()
        tm = self.theme_manager # Shorthand

        # Assumed ThemeManager properties (based on common patterns)
        # These should exist in your ThemeManager class
        tm.button_fg_color = getattr(tm, 'button_fg_color', tm.fg_color) 
        tm.accent_color_2 = getattr(tm, 'accent_color_2', tm.accent_color_1)
        tm.input_bg_color = getattr(tm, 'input_bg_color', tm.bg_color)
        tm.input_fg_color = getattr(tm, 'input_fg_color', tm.fg_color)
        tm.disabled_bg_color = getattr(tm, 'disabled_bg_color', tm.bg_color)
        tm.disabled_fg_color = getattr(tm, 'disabled_fg_color', tm.fg_color)


        default_font = ('Segoe UI', 9) 

        # Button Style
        style.configure("TButton", 
                        background=tm.accent_color_1, 
                        foreground=tm.button_fg_color,
                        padding=(8, 4, 8, 4), 
                        borderwidth=0, # Flat
                        relief=tk.FLAT,
                        font=default_font)
        style.map("TButton",
                  background=[('active', tm.accent_color_2), ('disabled', tm.disabled_bg_color)],
                  foreground=[('disabled', tm.disabled_fg_color)])

        # Combobox Style
        style.configure("TCombobox", 
                        fieldbackground=tm.input_bg_color, # Background of the entry field
                        foreground=tm.input_fg_color,
                        selectbackground=tm.accent_color_1, # Background of selected item in dropdown list
                        selectforeground=tm.button_fg_color, # Foreground of selected item in dropdown list
                        background=tm.input_bg_color, # Background of the arrow button
                        borderwidth=1, # Thin border for the field
                        relief=tk.SOLID, # Or tk.FLAT
                        padding=(6, 4, 6, 4),
                        font=default_font)
        style.map("TCombobox",
                  foreground=[('readonly', tm.input_fg_color), ('disabled', tm.disabled_fg_color)],
                  fieldbackground=[('readonly', tm.input_bg_color), ('disabled', tm.disabled_bg_color)],
                  background=[('readonly', tm.input_bg_color), ('disabled', tm.disabled_bg_color)])
        
        # Style for the Combobox dropdown list (via option_add)
        self.root.option_add('*TCombobox*Listbox.background', tm.input_bg_color)
        self.root.option_add('*TCombobox*Listbox.foreground', tm.input_fg_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', tm.accent_color_1)
        self.root.option_add('*TCombobox*Listbox.selectForeground', tm.button_fg_color)
        self.root.option_add('*TCombobox*Listbox.font', default_font)
        self.root.option_add('*TCombobox*Listbox.bd', 0) # No border for listbox
        self.root.option_add('*TCombobox*Listbox.relief', tk.FLAT)


        # Treeview Style (used in FileExplorerTab, define here for consistency)
        style.configure("Treeview", 
                        background=tm.input_bg_color, 
                        foreground=tm.fg_color,
                        fieldbackground=tm.input_bg_color, 
                        rowheight=28, # Increased row height
                        font=default_font,
                        borderwidth=0, # No border for treeview itself
                        relief=tk.FLAT)
        style.map("Treeview",
                  background=[('selected', tm.accent_color_1)],
                  foreground=[('selected', tm.button_fg_color)])
        
        style.configure("Treeview.Heading", 
                        background=tm.accent_color_1, 
                        foreground=tm.button_fg_color,
                        padding=(8, 8, 8, 8), # Increased padding for headings
                        borderwidth=0, # No border for headings
                        relief=tk.FLAT,
                        font=(default_font[0], default_font[1], 'bold'))
        style.map("Treeview.Heading",
                  background=[('active', tm.accent_color_2)])

        # Scrollbar Style (used in FileExplorerTab and TerminalTab)
        style.configure("TScrollbar", 
                        background=tm.bg_color, # Background of the scrollbar itself (not the arrows/slider)
                        troughcolor=tm.input_bg_color, 
                        bordercolor=tm.bg_color, 
                        arrowcolor=tm.fg_color, 
                        relief=tk.FLAT,
                        arrowsize=14) # Slightly larger arrows
        style.map("TScrollbar",
                  background=[('active', tm.accent_color_1)], # Slider color when active
                  arrowcolor=[('pressed', tm.accent_color_2), ('active', tm.button_fg_color)])
        
        # Notebook Style
        style.configure("TNotebook", 
                        background=tm.bg_color, 
                        borderwidth=0, # No border around the notebook
                        tabmargins=(0, 5, 0, 0)) # Margins around the tab area (l,t,r,b)
        style.configure("TNotebook.Tab", 
                        background=tm.input_bg_color, 
                        foreground=tm.fg_color,
                        padding=(12, 6, 12, 6), # Generous padding for tabs
                        borderwidth=0, # No border for individual tabs
                        font=(default_font[0], default_font[1], 'normal'))
        style.map("TNotebook.Tab",
                  background=[('selected', tm.accent_color_1), ('active', tm.accent_color_2)],
                  foreground=[('selected', tm.button_fg_color), ('active', tm.button_fg_color)],
                  font=[('selected', (default_font[0], default_font[1], 'bold'))])

        # General LabelFrame style (used in FileExplorerTab details)
        style.configure("TLabelFrame", 
                        background=tm.bg_color, 
                        foreground=tm.fg_color, 
                        borderwidth=1, 
                        relief=tk.SOLID, 
                        padding=(10, 10, 10, 10), # Padding inside the frame
                        font=default_font)
        style.configure("TLabelFrame.Label", 
                        background=tm.bg_color, 
                        foreground=tm.fg_color,
                        padding=(0,0,5,2), # Padding around the label widget itself (l,t,r,b)
                        font=(default_font[0], default_font[1], 'bold'))
        
        # General ttk.Label style (if used instead of tk.Label)
        style.configure("TLabel", 
                        background=tm.bg_color, 
                        foreground=tm.fg_color,
                        font=default_font)

        # TEntry Style (for ttk.Entry, if used)
        style.configure("TEntry",
                        fieldbackground=tm.input_bg_color,
                        foreground=tm.input_fg_color,
                        insertcolor=tm.fg_color, # Cursor color
                        borderwidth=1,
                        relief=tk.SOLID, # Or tk.FLAT
                        padding=(6,4,6,4),
                        font=default_font)
        style.map("TEntry",
                  bordercolor=[('focus', tm.accent_color_1)],
                  borderwidth=[('focus', 1)])


        # Checkbutton Style
        style.configure("TCheckbutton", 
                        background=tm.bg_color, 
                        foreground=tm.fg_color,
                        indicatorbackground=tm.input_bg_color,
                        indicatorforeground=tm.accent_color_1, # Color of the check mark
                        indicatordiameter=14, # Size of the check indicator
                        padding=(5, 5, 5, 5),
                        font=default_font)
        style.map("TCheckbutton",
                  indicatorbackground=[('selected', tm.input_bg_color), ('active', tm.input_bg_color)],
                  indicatorforeground=[('selected', tm.accent_color_1)], # Checkmark color when selected
                  background=[('active', tm.bg_color)]) # BG of label part when hovered

        # Radiobutton Style
        style.configure("TRadiobutton",
                        background=tm.bg_color,
                        foreground=tm.fg_color,
                        indicatorbackground=tm.input_bg_color,
                        indicatorforeground=tm.accent_color_1, # Color of the radio indicator when selected
                        indicatordiameter=14,
                        padding=(5, 2, 5, 2), # Adjusted padding
                        font=default_font)
        style.map("TRadiobutton",
                  indicatorbackground=[('selected', tm.input_bg_color), ('active', tm.input_bg_color)],
                  indicatorforeground=[('selected', tm.accent_color_1)],
                  background=[('active', tm.bg_color)])
    
    def _setup_bindings(self):
        """Set up event bindings"""
        self.server_dropdown.bind("<<ComboboxSelected>>", self._on_server_selected)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_callbacks(self):
        """Set up callbacks for SSH client"""
        # Set callbacks for SSH client
        self.ssh_client.on_output = self.terminal_tab.append_output
        self.ssh_client.on_status_change = self.status_var.set
        self.ssh_client.on_connection_state_change = self._on_connection_state_changed
        self.ssh_client.on_cpu_update = self.cpu_var.set
        self.ssh_client.on_memory_update = self.mem_var.set
        self.ssh_client.on_disk_update = self.disk_var.set
        
        # Set callbacks for SFTP operations
        self.sftp_ops.on_status_change = self.status_var.set
    
    def _on_close(self):
        """Handle window close event"""
        if self.ssh_client.connected:
            if messagebox.askyesno("Confirm Exit", 
                                  "You are still connected to the server. Disconnect and exit?"):
                
                self.status_var.set("Disconnecting and exiting...") # Immediate UI feedback

                def after_disconnect_callback(success, message):
                    if not success:
                        self.logger.log(f"Disconnection before exit failed or had issues: {message}")
                        # Optionally, inform the user if disconnection failed before exit, 
                        # though the window is closing anyway.
                        # messagebox.showwarning("Disconnect Issue", 
                        #                        f"Could not disconnect cleanly: {message}", 
                        #                        parent=self.root if self.root.winfo_exists() else None)
                    if self.root.winfo_exists(): # Check if root window still exists
                        self.root.destroy()

                # Call disconnect with the callback
                self.ssh_client.disconnect(on_complete_callback=after_disconnect_callback)
                # Do not call self.root.destroy() directly here anymore
            # else: User selected 'No', so don't close the window or disconnect
        else:
            # Not connected, so just destroy the window
            if self.root.winfo_exists(): 
                self.root.destroy()
    
    def _on_server_selected(self, event=None):
        """Handle server selection event"""
        selection = self.server_var.get()
        if not selection:
            return
        
        server_name = selection.split(" (")[0]
        servers = self.config.get("servers", {})
        
        if server_name in servers:
            server_info = servers[server_name]
            self.settings_tab.username_var.set(server_info["username"])
            self.settings_tab.hostname_var.set(server_info["hostname"])
            self.settings_tab.port_var.set(str(server_info["port"]))
    
    def _on_tab_changed(self, event=None):
        """Handle tab changed event"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        # If switching to File Explorer, refresh the view if connected
        if tab_text == "File Explorer" and self.ssh_client.connected:
            self.file_explorer_tab.refresh_view()
    
    def _on_connection_state_changed(self, connected, hostname, username):
        """Handle connection state changed"""
        if connected:
            self.server_name_var.set(f"SERVER: {username}@{hostname}")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            # Update config with last connection
            self.config.set("last_connection", {
                "hostname": hostname,
                "username": username
            })
            
            # Refresh file explorer if it's the current tab
            current_tab = self.notebook.select()
            tab_text = self.notebook.tab(current_tab, "text")
            if tab_text == "File Explorer":
                self.file_explorer_tab.refresh_view()
        else:
            self.server_name_var.set("SERVER: Not connected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.cpu_var.set("CPU: --")
            self.mem_var.set("MEM: --")
            self.disk_var.set("DISK: --")
    
    def _connect_selected(self):
        """Connect to the selected server"""
        self._on_server_selected()  # Ensure settings are up to date
        self._connect()
    
    def _connect(self):
        """Connect to the server with current settings"""
        hostname = self.settings_tab.hostname_var.get()
        username = self.settings_tab.username_var.get()
        
        try:
            port = int(self.settings_tab.port_var.get())
        except ValueError:
            port = 22
        
        password = self.settings_tab.password_var.get()
        key_path = self.settings_tab.key_path_var.get()
        
        # If no password, prompt for it
        if not password and not key_path:
            from tkinter import simpledialog
            password = simpledialog.askstring(
                "SSH Password",
                f"Enter password for {username}@{hostname}:",
                show='*'
            )
            if not password:
                return
        
        # Save password if remember is checked
        if self.settings_tab.remember_var.get() and password:
            self.config.set("password", password)
            self.settings_tab.password_var.set(password)
        
        # Connect
        self.ssh_client.connect(
            hostname=hostname,
            username=username,
            port=port,
            password=password,
            key_path=key_path
        )
    
    def _disconnect(self):
        """Disconnect from the server"""
        if not self.ssh_client.connected:
            return
        
        self.ssh_client.disconnect()
    
    def _auto_connect(self):
        """Auto-connect to the last server"""
        self._connect_selected()