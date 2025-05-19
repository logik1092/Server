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
                 fg=self.theme_manager.fg_color).pack(side=tk.LEFT, padx=5)
        
        # Get server options
        servers = self.config.get("servers", {})
        server_options = [f"{name} ({info['username']}@{info['hostname']})" 
                          for name, info in servers.items()]
        
        self.server_var = tk.StringVar()
        self.server_dropdown = ttk.Combobox(self.server_frame, 
                                           textvariable=self.server_var, 
                                           values=server_options)
        self.server_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        if server_options:
            self.server_dropdown.current(0)
        
        # Connect button
        self.connect_btn = ttk.Button(self.server_frame, text="Connect", 
                                     command=self._connect_selected)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Disconnect button
        self.disconnect_btn = ttk.Button(self.server_frame, text="Disconnect", 
                                        command=self._disconnect,
                                        state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
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
        self.monitor_frame = tk.Frame(self.main_frame, bg="#2d2d2d", height=25)
        self.monitor_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Status variables
        self.server_name_var = tk.StringVar(value="SERVER: Not connected")
        self.cpu_var = tk.StringVar(value="CPU: --")
        self.mem_var = tk.StringVar(value="MEM: --")
        self.disk_var = tk.StringVar(value="DISK: --")
        
        # Status labels
        tk.Label(self.monitor_frame, textvariable=self.server_name_var, 
                bg="#2d2d2d", fg="#77ccff", padx=10).pack(side=tk.LEFT)
        tk.Label(self.monitor_frame, textvariable=self.cpu_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color, padx=10).pack(side=tk.LEFT)
        tk.Label(self.monitor_frame, textvariable=self.mem_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color, padx=10).pack(side=tk.LEFT)
        tk.Label(self.monitor_frame, textvariable=self.disk_var, 
                bg="#2d2d2d", fg=self.theme_manager.fg_color, padx=10).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Not connected")
        self.status_bar = tk.Label(self.main_frame, textvariable=self.status_var, 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                  bg="#2d2d2d", fg=self.theme_manager.fg_color)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
        
        # Set up callbacks
        self._setup_callbacks()
    
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