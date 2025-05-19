"""
File: myforge_terminal/ssh/client.py
Description: SSH Client Module - Handles SSH connections and operations

Structure:
  Classes:
    SSHClient:
      Description: Initialize SSH client with configuration and logger
      - __init__(self, config, logger)
      - connect(self, hostname, username, port=22, password=None, key_path=None, on_complete=None)
      - disconnect(self, on_complete_callback=None)
      - send_command(self, command, store_in_history=True)
      - get_sftp_client(self)
      - close_sftp(self)
"""

import threading
import socket
import time
import re
import paramiko
from utils.logger import Logger

class SSHClient:
    def __init__(self, config, logger):
        """Initialize SSH client with configuration and logger"""
        self.config = config
        self.logger = logger
        self.disconnect_lock = threading.Lock()
        
        # Connection objects
        self.client = None
        self.shell = None
        self.sftp = None
        
        # Connection state
        self.connected = False
        self.hostname = None
        self.username = None
        self.port = None
        
        # Output callbacks
        self.on_output = None
        self.on_status_change = None
        self.on_connection_state_change = None
        
        # Process management
        self.known_processes = {}  # Store PIDs of launched processes

    def connect(self, hostname, username, port=22, password=None, key_path=None, on_complete=None):
        """
        Connect to an SSH server
        
        Args:
            hostname: Server hostname or IP
            username: SSH username
            port: SSH port (default: 22)
            password: SSH password (optional)
            key_path: Path to SSH private key (optional)
            on_complete: Callback function to run after connection attempt
        """
        self.hostname = hostname
        self.username = username
        self.port = port
        
        def connect_thread():
            success = False
            error_message = None
            
            try:
                if self.on_status_change:
                    self.on_status_change(f"Connecting to {hostname}...")
                
                # Create SSH client
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Prepare connection parameters
                connect_params = {
                    "hostname": hostname,
                    "port": port,
                    "username": username
                }
                
                # Add authentication
                if key_path and key_path.strip():
                    connect_params["key_filename"] = key_path
                    if password:  # Use as key passphrase
                        connect_params["passphrase"] = password
                elif password:
                    connect_params["password"] = password
                else:
                    error_message = "No password or SSH key provided"
                    self.logger.log(f"Connection error: {error_message}")
                    if on_complete:
                        on_complete(False, error_message)
                    return
                
                # Attempt connection
                self.client.connect(**connect_params)
                
                # Get shell and SFTP channels
                self.shell = self.client.invoke_shell()
                self.shell.settimeout(0.1)  # Small timeout for non-blocking reads
                
                # Successful connection
                self.connected = True
                
                # Start output reading thread
                threading.Thread(target=self._read_output, daemon=True).start()
                
                # Send initial commands
                self._send_welcome_commands()
                
                # Log success
                success = True
                self.logger.log(f"Connected to {hostname}")
                
                # Update status
                if self.on_status_change:
                    self.on_status_change(f"Connected to {hostname}")
                
                # Notify about connection state
                if self.on_connection_state_change:
                    self.on_connection_state_change(True, hostname, username)
                
            except paramiko.ssh_exception.AuthenticationException as e:
                error_message = f"Authentication failed: {str(e)}"
                self.logger.log(error_message)
                if self.on_status_change:
                    self.on_status_change("Authentication failed")
            except Exception as e:
                error_message = f"Connection error: {str(e)}"
                self.logger.log(error_message)
                if self.on_status_change:
                    self.on_status_change("Connection failed")
            
            # Run completion callback
            if on_complete:
                on_complete(success, error_message)
        
        # Start connection in a separate thread
        threading.Thread(target=connect_thread, daemon=True).start()

    def disconnect(self, on_complete_callback=None):
        """Disconnect from the SSH server, performing blocking operations in a thread."""
        if not self.disconnect_lock.acquire(blocking=False):
            self.logger.log("Disconnect operation already in progress.")
            if on_complete_callback:
                on_complete_callback(False, "Disconnect operation already in progress.")
            return

        if not self.connected:
            self.logger.log("Not connected or already disconnected.")
            self.disconnect_lock.release()
            if on_complete_callback:
                on_complete_callback(True, "Not connected or already disconnected.")
            return

        self.logger.log(f"Initiating disconnect from {self.hostname}...")
        self.connected = False  # Signal other threads to stop

        def disconnect_thread_worker():
            try:
                if self.on_status_change:
                    self.on_status_change("Disconnecting...")

                time.sleep(0.2) # Brief pause for other threads to observe self.connected = False

                resources_closed_properly = True
                
                current_shell = self.shell
                self.shell = None # Nullify before closing to help loops exit
                if current_shell:
                    try:
                        if not current_shell.closed:
                            current_shell.close()
                    except Exception as e:
                        self.logger.log(f"Error closing shell: {str(e)}")
                        resources_closed_properly = False
                
                current_sftp = self.sftp
                self.sftp = None # Nullify before closing
                if current_sftp:
                    try:
                        current_sftp.close()
                    except Exception as e:
                        self.logger.log(f"Error closing SFTP: {str(e)}")
                        resources_closed_properly = False
                
                current_client = self.client
                self.client = None # Nullify before closing
                if current_client:
                    try:
                        current_client.close()
                    except Exception as e:
                        self.logger.log(f"Error closing SSH client: {str(e)}")
                        resources_closed_properly = False
                
                self.logger.log(f"Disconnected resources for {self.hostname}.")
                
                if self.on_status_change:
                    self.on_status_change("Disconnected")
                if self.on_connection_state_change:
                    self.on_connection_state_change(False, self.hostname, self.username) # Pass original host/user for context
                if self.on_output:
                    self.on_output(f"[Disconnected from {self.username}@{self.hostname}]\n")
                
                if on_complete_callback:
                    on_complete_callback(resources_closed_properly, None if resources_closed_properly else "Error closing some resources.")

            except Exception as e:
                self.logger.log(f"Unhandled error during disconnect thread: {str(e)}")
                if self.on_status_change:
                    self.on_status_change(f"Error during disconnect: {str(e)}")
                if on_complete_callback:
                    on_complete_callback(False, str(e))
            finally:
                self.disconnect_lock.release()

        threading.Thread(target=disconnect_thread_worker, daemon=True).start()

    def send_command(self, command, store_in_history=True):
        """
        Send a command to the SSH server
        
        Args:
            command: Command to send
            store_in_history: Whether to store command in history
        """
        if not self.connected or not self.shell:
            if self.on_output:
                self.on_output("[Not connected to server]\n")
            return False
        
        try:
            # Check for process control commands
            if command.startswith("kill-process:"):
                return self._handle_process_kill(command)
                
            # Send command
            self.shell.send(command + "\n")
            
            # Log command
            self.logger.log(f"Command: {command}")
            
            return True
        
        except Exception as e:
            if self.on_output:
                self.on_output(f"[Error sending command] {str(e)}\n")
            self.logger.log(f"Error sending command: {str(e)}")
            return False

    def _handle_process_kill(self, command):
        """Handle special kill-process command"""
        try:
            # Format: kill-process:pid
            parts = command.split(':')
            if len(parts) != 2:
                return False
            
            pid = parts[1].strip()
            self.shell.send(f"kill {pid}\n")
            self.logger.log(f"Killed process with PID: {pid}")
            
            # Remove from known processes
            for name, stored_pid in list(self.known_processes.items()):
                if stored_pid == pid:
                    del self.known_processes[name]
                    if self.on_output:
                        self.on_output(f"[Killed process: {name} (PID: {pid})]\n")
                    break
            
            return True
        except Exception as e:
            self.logger.log(f"Error killing process: {str(e)}")
            return False

    def _read_output(self):
        """Read output from SSH shell channel"""
        buffer = ""
        
        # Check self.shell and self.shell.closed more robustly
        while self.connected and self.shell and not self.shell.closed:
            try:
                if self.shell.recv_ready():
                    data = self.shell.recv(4096).decode('utf-8', errors='replace')
                    if not data: # Connection might have been closed by server
                        if not self.shell.closed: # Check if shell is actually closed
                             time.sleep(0.01) # Small pause if no data but shell not marked closed
                        continue
                    
                    # Send output to callback
                    if self.on_output:
                        self.on_output(data)
                    
                    # Process output for special patterns
                    buffer += data
                    if '\n' in buffer:
                        lines = buffer.split('\n')
                        buffer = lines[-1]  # Keep incomplete line
                        
                        for line in lines[:-1]:
                            self._process_output_line(line)
                
                # Check if shell closed by remote end or due to error
                elif self.shell.exit_status_ready() or self.shell.closed:
                    self.logger.log("Shell exit status ready or shell closed, terminating output reading.")
                    self.connected = False # Ensure loop terminates
                    break
            
            except socket.timeout:
                # Expected due to timeout setting, continue if still connected
                if not self.connected or (self.shell and self.shell.closed):
                    break
                pass
            except Exception as e:
                if self.connected: # Log error only if we expected to be connected
                    if self.on_output:
                        self.on_output(f"[Error reading from server] {str(e)}\n")
                    self.logger.log(f"Error reading from server: {str(e)}. Initiating disconnect.")
                    self.disconnect() # This will use the new threaded disconnect
                break # Exit loop on error
        
        self.logger.log(f"_read_output loop finished. Connected: {self.connected}, Shell: {self.shell}")
        # If loop exited but still marked as connected (e.g. self.shell became None externally)
        if self.connected and not self.shell: # If shell is None, we can't read.
             self.logger.log("Shell is None while connected, signaling disconnect.")
             self.connected = False # Signal to stop. Disconnect process should handle full cleanup.

    def _process_output_line(self, line):
        """Process a single line of output for special patterns"""
        # Look for process IDs in output
        if "server started" in line.lower() or "uvicorn" in line.lower():
            pid_match = re.search(r'process ID[:=\s]*(\d+)', line, re.IGNORECASE)
            if pid_match:
                pid = pid_match.group(1)
                process_name = "uvicorn" if "uvicorn" in line.lower() else "server"
                self.known_processes[process_name] = pid
                self.logger.log(f"Detected {process_name} process with PID: {pid}")
        
        # Extract CPU info from 'uptime'
        if "load average:" in line:
            match = re.search(r'load average:\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)', line)
            if match:
                load1 = match.group(1)
                self._update_system_stat("cpu", f"CPU Load: {load1}")
        
        # Extract memory info from 'free -h'
        if line.startswith("Mem:"):
            parts = line.split()
            if len(parts) >= 4:  # Need at least Mem:, total, used, free
                total_mem, used_mem = parts[1], parts[2]
                self._update_system_stat("memory", f"Memory: {used_mem}/{total_mem}")
        
        # Extract disk info
        parts = line.split()
        if len(parts) >= 5 and parts[-1] == "/":
            disk_usage_percent = parts[-2]  # Percentage used
            used_disk, total_disk = parts[2], parts[1]  # Used and Total
            self._update_system_stat("disk", f"Disk: {disk_usage_percent} ({used_disk}/{total_disk})")

    def _update_system_stat(self, stat_type, value):
        """Update system statistics via callback"""
        if hasattr(self, f"on_{stat_type}_update") and callable(getattr(self, f"on_{stat_type}_update")):
            callback = getattr(self, f"on_{stat_type}_update")
            callback(value)
    
    def _send_welcome_commands(self):
        """Send initial commands after connection"""
        # Start system monitoring
        threading.Thread(target=self._monitor_system, daemon=True).start()
    
    def _monitor_system(self):
        """Periodically check system status"""
        interval = 60  # seconds between updates
        
        # Check self.shell and self.shell.closed more robustly
        while self.connected and self.shell and not self.shell.closed:
            try:
                # Send commands to check system status
                # Ensure shell is usable before sending
                if self.shell and not self.shell.closed and self.shell.send_ready():
                    self.shell.send("uptime\n")
                    time.sleep(0.2) # Give time for command to be processed
                    if not (self.connected and self.shell and not self.shell.closed and self.shell.send_ready()): break
                    self.shell.send("free -h | grep '^Mem:'\n")
                    time.sleep(0.2)
                    if not (self.connected and self.shell and not self.shell.closed and self.shell.send_ready()): break
                    self.shell.send("df -h / | tail -n 1\n")
                else:
                    self.logger.log("System monitor: Shell not ready or closed, skipping command send.")
                    break # Exit if shell is not usable
                
                # Wait for next update
                for _ in range(interval):
                    if not self.connected or (self.shell and self.shell.closed):
                        break
                    time.sleep(1)
            except Exception as e:
                if self.connected and self.shell and not self.shell.closed : # Log error only if we expected to be active
                    self.logger.log(f"Error in system monitoring: {e}")
                break # Exit loop on error
        self.logger.log(f"_monitor_system loop finished. Connected: {self.connected}, Shell: {self.shell}")

    
    def get_sftp_client(self):
        """Get or create SFTP client with error handling"""
        if not self.connected:
            return None
        
        try:
            if not self.sftp or self.sftp.sock.closed:
                self.logger.log("Creating new SFTP client")
                self.sftp = self.client.open_sftp()
                self.sftp.sock.settimeout(30)  # 30 second timeout for operations
            return self.sftp
        except Exception as e:
            self.logger.log(f"Error creating SFTP client: {str(e)}", level='error')
            # Attempt to re-establish SSH connection if it failed
            if str(e).lower().find('not connected') >= 0 or str(e).lower().find('eof') >= 0:
                self.logger.log("SSH connection appears broken, marking as disconnected")
                self.connected = False
            return None
    
        
        try:
            if not self.sftp or self.sftp.sock.closed:
                self.sftp = self.client.open_sftp()
            return self.sftp
        except Exception as e:
            self.logger.log(f"Error creating SFTP client: {str(e)}")
            return None
    
    def close_sftp(self):
        """Close SFTP connection if open"""
        if self.sftp:
            try:
                self.sftp.close()
                self.sftp = None
            except Exception as e:
                self.logger.log(f"Error closing SFTP: {str(e)}")