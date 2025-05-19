import os
import re

def fix_sftp_py():
    """Fix issues in sftp.py"""
    sftp_path = os.path.join("ssh", "sftp.py")
    
    with open(sftp_path, 'r') as f:
        content = f.read()
    
    # Fix syntax error on line 262
    content = content.replace(
        'self.logger.log(f"SFTP: Error creating sub-directory {dir_path}: {str(e)}\\"',
        'self.logger.log(f"SFTP: Error creating sub-directory {dir_path}: {str(e)}"'
    )
    
    # Fix thread daemon setting
    content = content.replace(
        'download_thread_obj.daemon = False',
        'download_thread_obj.daemon = True'
    )
    
    # Add retry logic for SFTP connection
    connection_logic = '''
        sftp = None
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries and not sftp:
            try:
                sftp = self.ssh_client.get_sftp_client()
                if not sftp:
                    retry_count += 1
                    time.sleep(1)  # Brief pause before retry
                else:
                    break
            except Exception as e:
                self.logger.log(f"SFTP: Retry {retry_count+1} failed: {e}", level='warning')
                retry_count += 1
                time.sleep(1)  # Brief pause before retry
        
        if not sftp:
            # Final failure after retries
            if on_complete:
                on_complete(False, 0, 0, "Could not establish SFTP connection after multiple attempts")
            return'''
    
    # Replace simple sftp connection check with retry logic
    content = re.sub(
        r'sftp = self\.ssh_client\.get_sftp_client\(\)\s+if not sftp:.*?return',
        connection_logic,
        content,
        flags=re.DOTALL
    )
    
    # Add file download retry logic
    file_retry_logic = '''
                try:
                    # Create parent directory if it doesn't exist
                    local_dir_path = os.path.dirname(local_path)
                    if not os.path.exists(local_dir_path):
                        os.makedirs(local_dir_path)
                    
                    # Download with retry
                    retry_count = 0
                    max_file_retries = 2
                    file_downloaded = False
                    
                    while not file_downloaded and retry_count <= max_file_retries:
                        try:
                            self.logger.debug(f"SFTP: Attempting download of {remote_path}, attempt {retry_count+1}")
                            sftp.stat(remote_path)  # Verify existence
                            sftp.get(remote_path, local_path, callback=lambda current, total, 
                                    fn=file_name, rp=remote_path, lp=local_path: 
                                    self._download_progress(current, total, fn, rp, lp, on_progress))
                            
                            file_downloaded = True
                            downloaded_files += 1
                            self.logger.debug(f"SFTP: Downloaded {remote_path}")
                        except Exception as dl_e:
                            retry_count += 1
                            self.logger.log(f"SFTP: Download attempt {retry_count} failed for {remote_path}: {str(dl_e)}")
                            if retry_count <= max_file_retries:
                                time.sleep(1)  # Brief pause before retry
                                try:
                                    # Try to refresh SFTP connection
                                    sftp = self.ssh_client.get_sftp_client()
                                except Exception:
                                    pass
                            else:
                                raise  # Re-raise to be caught by outer exception handler
                
                except Exception as e:
                    failed_files += 1
                    self.logger.log(f"SFTP: Error downloading {remote_path}: {str(e)}", level='error')'''
    
    # Replace the download attempt block with retry logic
    content = re.sub(
        r'try:\s+local_dir_path = os\.path\.dirname\(local_path\).*?self\.logger\.debug\(f"SFTP: Downloaded \{remote_path\}"\)\s+except Exception as e:.*?self\.logger\.log\(f"SFTP: Exception re-establishing SFTP: \{recon_e\}", level=\'error\'\)',
        file_retry_logic,
        content,
        flags=re.DOTALL
    )
    
    # Fix progress callback to ensure UI updates on main thread
    progress_callback = '''
    def _download_progress(self, transferred, total, filename, remote_path, local_path, callback=None):
        """Handle download progress updates"""
        if total == 0:  # Avoid division by zero
            percent = 100
        else:
            percent = (transferred / total) * 100
        
        # Don't update UI directly from thread - callback will handle that
        if callback:
            callback(filename, transferred, total, percent)
    '''
    
    # Replace the progress method with improved one
    content = re.sub(
        r'def _download_progress\(self, transferred, total, filename, remote_path, local_path, callback=None\):.*?if callback:.*?callback\(filename, transferred, total, percent\)',
        progress_callback,
        content,
        flags=re.DOTALL
    )
    
    with open(sftp_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {sftp_path}")

def fix_file_explorer_tab_py():
    """Fix issues in file_explorer_tab.py"""
    tab_path = os.path.join("ui", "file_explorer_tab.py")
    
    with open(tab_path, 'r') as f:
        content = f.read()
    
    # Ensure progress updates happen on main thread
    content = re.sub(
        r'def on_progress\(filename, transferred, total, percent\):.*?progress_dialog\.update_progress\(',
        'def on_progress(filename, transferred, total, percent):\n            # Ensure UI updates happen on the main thread\n            self.frame.after(0, lambda: progress_dialog.update_progress(',
        content,
        flags=re.DOTALL
    )
    
    # Add error handling for SFTP operations
    content = re.sub(
        r'# Start download.*?self\.sftp_ops\.download_files\(',
        '# Start download with error handling\n        try:\n            self.sftp_ops.download_files(',
        content,
        flags=re.DOTALL
    )
    
    with open(tab_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {tab_path}")

def fix_client_py():
    """Fix issues in client.py"""
    client_path = os.path.join("ssh", "client.py")
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Improve SFTP client handling
    better_sftp = '''
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
    '''
    
    # Replace the get_sftp_client method with improved one
    content = re.sub(
        r'def get_sftp_client\(self\):.*?return None',
        better_sftp,
        content,
        flags=re.DOTALL
    )
    
    with open(client_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {client_path}")

if __name__ == "__main__":
    print("Applying fixes to MyForge Terminal...")
    fix_sftp_py()
    fix_file_explorer_tab_py()
    fix_client_py()
    print("Fixes completed! Please restart the application.")