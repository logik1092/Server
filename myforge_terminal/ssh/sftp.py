"""
File: myforge_terminal/ssh/sftp.py
Description: SFTP Operations Module - Handles SFTP file transfer and browsing operations

Structure:
  Classes:
    SFTPOperations:
      Description: Initialize SFTP operations with SSH client and logger
      - __init__(self, ssh_client, logger)
      - list_directory(self, remote_path=None, on_complete=None)
      - download_files(self, items, local_dir, on_progress=None, on_complete=None)
      - upload_files(self, local_files, remote_dir, overwrite=False, on_progress=None, on_complete=None)
      - create_directory(self, remote_parent_dir, new_dir_name, on_complete=None)
      - delete_item(self, item, on_complete=None)
      - rename_item(self, item, new_name, on_complete=None)
      - get_file_content(self, remote_path, on_complete=None)
      - save_file_content(self, remote_path, content, on_complete=None)
"""

import os
import threading
import posixpath
import stat
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class SFTPOperations:
    def __init__(self, ssh_client, logger):
        """Initialize SFTP operations with SSH client and logger"""
        self.ssh_client = ssh_client
        self.logger = logger
        
        # Callbacks
        self.on_progress = None
        self.on_status_change = None
        self.on_operation_complete = None
        
        # Path tracking
        self.default_remote_path = "/var/www/myforge.ai"
        self.current_remote_path = self.default_remote_path
    
    def list_directory(self, remote_path=None, on_complete=None):
        """
        List files in a remote directory
        
        Args:
            remote_path (str, optional): Remote path to list. Defaults to current path.
            on_complete (callable): Callback with (success, items, error) parameters
        """
        if remote_path is None:
            remote_path = self.current_remote_path
        
        def list_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, [], "Could not establish SFTP connection")
                return
            
            try:
                self.logger.log(f"Listing directory: {remote_path}")
                
                if self.on_status_change:
                    self.on_status_change(f"Listing {remote_path}...")
                
                # Get directory contents with attributes
                dir_items = sftp.listdir_attr(remote_path)
                
                # Process items
                items = []
                
                # Add parent directory entry if not at root
                if remote_path != '/' and remote_path != sftp.normalize('/'):
                    parent_path = posixpath.normpath(posixpath.join(remote_path, '..'))
                    if parent_path != remote_path:  # Avoid '..' if it leads to the same dir
                        items.append({
                            'name': '..',
                            'path': parent_path,
                            'type': 'directory',
                            'size': 0,
                            'modified': 0,
                            'permissions': '',
                            'is_parent': True
                        })
                
                # Sort directories first, then files
                dirs = []
                files = []
                
                for item in dir_items:
                    full_path = posixpath.join(remote_path, item.filename)
                    
                    # Get file type
                    if stat.S_ISDIR(item.st_mode):
                        item_type = 'directory'
                    elif stat.S_ISLNK(item.st_mode):
                        item_type = 'link'
                    else:
                        item_type = 'file'
                    
                    # Format permissions string
                    perm_string = self._format_permissions(item.st_mode)
                    
                    # Convert modification time
                    try:
                        mod_time = datetime.fromtimestamp(item.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        mod_time = 'Unknown'
                    
                    item_info = {
                        'name': item.filename,
                        'path': full_path,
                        'type': item_type,
                        'size': item.st_size,
                        'modified': mod_time,
                        'permissions': perm_string,
                        'is_parent': False
                    }
                    
                    if item_type == 'directory':
                        dirs.append(item_info)
                    else:
                        files.append(item_info)
                
                # Sort by name (case-insensitive)
                dirs.sort(key=lambda x: x['name'].lower())
                files.sort(key=lambda x: x['name'].lower())
                
                # Combine lists (directories first, then files)
                items.extend(dirs)
                items.extend(files)
                
                # Update current path if successful
                self.current_remote_path = remote_path
                
                # Reset status
                if self.on_status_change:
                    self.on_status_change(f"Connected to {self.ssh_client.hostname}")
                
                # Call completion callback
                if on_complete:
                    on_complete(True, items, None)
                
                self.logger.log(f"Listed directory {remote_path}: {len(items)} items")
                
            except Exception as e:
                error_msg = f"Error listing directory {remote_path}: {str(e)}"
                self.logger.log(error_msg)
                
                if self.on_status_change:
                    self.on_status_change(f"Error listing directory")
                
                if on_complete:
                    on_complete(False, [], error_msg)
        
        # Run in a separate thread
        threading.Thread(target=list_thread, daemon=True).start()
    
    def download_files(self, items, local_dir, on_progress=None, on_complete=None):
        """
        Download files and directories to a local directory
        
        Args:
            items: List of item dictionaries to download
            local_dir: Local directory to save files
            on_progress: Progress callback function
            on_complete: Completion callback function
        """
        def download_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, 0, 0, "Could not establish SFTP connection")
                return
            
            try:
                total_files = 0
                downloaded_files = 0
                failed_files = 0
                
                # Count total files (including in subdirectories)
                files_to_download = []
                dirs_to_create = []
                
                for item in items:
                    if item.get('is_parent', False):
                        continue  # Skip parent directory entry
                    
                    if item['type'] == 'directory':
                        # Process directory recursively
                        self._count_dir_files(sftp, item['path'], files_to_download, dirs_to_create, 
                                             local_dir, item['name'])
                    else:
                        # Add file to download list
                        total_files += 1
                        files_to_download.append({
                            'remote_path': item['path'],
                            'local_path': os.path.join(local_dir, item['name']),
                            'name': item['name']
                        })
                
                self.logger.log(f"SFTP: Populated dirs_to_create: {dirs_to_create}")
                self.logger.log(f"SFTP: Populated files_to_download (count: {len(files_to_download)}): {files_to_download}")
                
                # Create all necessary directories
                for dir_path in dirs_to_create:
                    try:
                        dir_path = os.path.normpath(dir_path)  # Normalize path separators
                        if not os.path.exists(dir_path):
                            os.makedirs(dir_path, exist_ok=True)
                            self.logger.log(f"SFTP: Created directory {dir_path}")
                    except Exception as e:
                        self.logger.log(f"SFTP: Error creating sub-directory {dir_path}: {str(e)}")
                
                # Download files
                for i, file_info in enumerate(files_to_download):
                    remote_path = file_info['remote_path'] # Initialize remote_path
                    local_path = file_info['local_path']
                    file_name = file_info['name']
                    
                    # Fix Windows paths - normalize separators
                    local_path = os.path.normpath(local_path)
                    remote_path = remote_path.replace('\\', '/') # Ensure remote_path uses forward slashes

                    if self.on_status_change:
                        self.on_status_change(f"Downloading {file_name} ({i+1}/{len(files_to_download)})...")
                    
                    try:
                        # Create parent directory with explicit creation
                        local_dir_path = os.path.dirname(local_path)
                        if local_dir_path and not os.path.exists(local_dir_path):
                            try:
                                # Use makedirs with exist_ok to handle race conditions
                                os.makedirs(local_dir_path, exist_ok=True)
                                self.logger.log(f"SFTP: Created directory structure: {local_dir_path}")
                            except Exception as dir_e:
                                self.logger.log(f"SFTP: Error creating directory {local_dir_path}: {str(dir_e)}")
                                # Continue anyway, maybe the file creation will work
                        
                        # Download with retry
                        retry_count = 0
                        max_file_retries = 2
                        file_downloaded = False
                        
                        while not file_downloaded and retry_count <= max_file_retries:
                            try:
                                self.logger.log(f"SFTP: Attempting download of {remote_path} to {local_path}, attempt {retry_count+1}")
                                sftp.stat(remote_path)  # Verify existence
                                sftp.get(remote_path, local_path, callback=lambda current, total, 
                                        fn=file_name, rp=remote_path, lp=local_path: 
                                        self._download_progress(current, total, fn, rp, lp, on_progress))
                                
                                file_downloaded = True
                                downloaded_files += 1
                                self.logger.log(f"SFTP: Downloaded {remote_path} to {local_path}")
                            except Exception as dl_e:
                                retry_count += 1
                                self.logger.log(f"SFTP: Download attempt {retry_count} failed for {remote_path} to {local_path}: {str(dl_e)}")
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
                        self.logger.log(f"SFTP: Error downloading remote file '{remote_path}' to local file '{local_path}': {str(e)}")
                
                # Final status update
                success = failed_files == 0
                status_msg = (f"Download complete: {downloaded_files} files downloaded"
                              f"{f', {failed_files} failed' if failed_files > 0 else ''}")
                
                if self.on_status_change:
                    self.on_status_change(status_msg)
                
                if on_complete:
                    on_complete(success, downloaded_files, failed_files, 
                               None if success else "Some files failed to download")
                
                self.logger.log(status_msg)
            
            except Exception as e:
                error_msg = f"Error during download operation: {str(e)}"
                self.logger.log(error_msg)
                
                if self.on_status_change:
                    self.on_status_change("Download failed")
                
                if on_complete:
                    on_complete(False, 0, 0, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=download_thread, daemon=True).start()
    
    def upload_files(self, local_files, remote_dir, overwrite=False, on_progress=None, on_complete=None):
        """
        Upload local files to a remote directory
        
        Args:
            local_files: List of local file paths to upload
            remote_dir: Remote directory to upload to
            overwrite: Whether to overwrite existing files
            on_progress: Progress callback function
            on_complete: Completion callback function
        """
        def upload_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, 0, 0, "Could not establish SFTP connection")
                return
            
            try:
                total_files = len(local_files)
                uploaded_files = 0
                failed_files = 0
                skipped_files = 0
                
                for i, local_path in enumerate(local_files):
                    file_name = os.path.basename(local_path)
                    remote_path = posixpath.join(remote_dir, file_name)
                    
                    if self.on_status_change:
                        self.on_status_change(f"Uploading {file_name} ({i+1}/{total_files})...")
                    
                    try:
                        # Check if file exists
                        file_exists = False
                        try:
                            sftp.stat(remote_path)
                            file_exists = True
                        except:
                            pass
                        
                        if file_exists and not overwrite:
                            skipped_files += 1
                            self.logger.log(f"Skipped {local_path} (already exists)")
                            continue
                        
                        # Upload file with progress tracking
                        sftp.put(local_path, remote_path, callback=lambda current, total, 
                                fn=file_name, rp=remote_path, lp=local_path: 
                                self._upload_progress(current, total, fn, rp, lp, on_progress))
                        
                        uploaded_files += 1
                        self.logger.log(f"Uploaded {local_path} to {remote_path}")
                    
                    except Exception as e:
                        failed_files += 1
                        self.logger.log(f"Error uploading {local_path}: {str(e)}")
                
                # Final status update
                success = failed_files == 0
                status_msg = (f"Upload complete: {uploaded_files} files uploaded"
                              f"{f', {skipped_files} skipped' if skipped_files > 0 else ''}"
                              f"{f', {failed_files} failed' if failed_files > 0 else ''}")
                
                if self.on_status_change:
                    self.on_status_change(status_msg)
                
                if on_complete:
                    on_complete(success, uploaded_files, failed_files, 
                               None if success else "Some files failed to upload")
                
                self.logger.log(status_msg)
                
                # Refresh directory listing if upload successful
                if success and uploaded_files > 0:
                    self.list_directory(remote_dir)
            
            except Exception as e:
                error_msg = f"Error during upload operation: {str(e)}"
                self.logger.log(error_msg)
                
                if self.on_status_change:
                    self.on_status_change("Upload failed")
                
                if on_complete:
                    on_complete(False, 0, 0, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def create_directory(self, remote_parent_dir, new_dir_name, on_complete=None):
        """
        Create a new directory on the remote server
        
        Args:
            remote_parent_dir: Parent directory path
            new_dir_name: Name of new directory
            on_complete: Completion callback function
        """
        def create_dir_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, "Could not establish SFTP connection")
                return
            
            try:
                remote_path = posixpath.join(remote_parent_dir, new_dir_name)
                
                # Check if directory already exists
                try:
                    sftp.stat(remote_path)
                    if on_complete:
                        on_complete(False, f"Directory {new_dir_name} already exists")
                    return
                except:
                    pass
                
                # Create directory
                sftp.mkdir(remote_path)
                self.logger.log(f"Created directory {remote_path}")
                
                if on_complete:
                    on_complete(True, None)
                
                # Refresh directory listing
                self.list_directory(remote_parent_dir)
            
            except Exception as e:
                error_msg = f"Error creating directory {new_dir_name}: {str(e)}"
                self.logger.log(error_msg)
                
                if on_complete:
                    on_complete(False, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=create_dir_thread, daemon=True).start()
    
    def delete_item(self, item, on_complete=None):
        """
        Delete a file or directory on the remote server
        
        Args:
            item: Item dictionary with path and type
            on_complete: Completion callback function
        """
        def delete_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, "Could not establish SFTP connection")
                return
            
            try:
                remote_path = item['path']
                item_type = item['type']
                
                if item_type == 'directory':
                    # Recursively delete directory contents
                    self._delete_directory_recursive(sftp, remote_path)
                else:
                    # Delete file
                    sftp.remove(remote_path)
                
                self.logger.log(f"Deleted {item_type} {remote_path}")
                
                if on_complete:
                    on_complete(True, None)
                
                # Refresh parent directory listing
                parent_dir = posixpath.dirname(remote_path)
                self.list_directory(parent_dir)
            
            except Exception as e:
                error_msg = f"Error deleting {item['path']}: {str(e)}"
                self.logger.log(error_msg)
                
                if on_complete:
                    on_complete(False, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def rename_item(self, item, new_name, on_complete=None):
        """
        Rename a file or directory on the remote server
        
        Args:
            item: Item dictionary with path and type
            new_name: New name for the item
            on_complete: Completion callback function
        """
        def rename_thread():
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, "Could not establish SFTP connection")
                return
            
            try:
                old_path = item['path']
                parent_dir = posixpath.dirname(old_path)
                new_path = posixpath.join(parent_dir, new_name)
                
                # Check if target already exists
                try:
                    sftp.stat(new_path)
                    if on_complete:
                        on_complete(False, f"A file or directory named {new_name} already exists")
                    return
                except:
                    pass
                
                # Rename
                sftp.rename(old_path, new_path)
                self.logger.log(f"Renamed {old_path} to {new_path}")
                
                if on_complete:
                    on_complete(True, None)
                
                # Refresh directory listing
                self.list_directory(parent_dir)
            
            except Exception as e:
                error_msg = f"Error renaming {item['path']}: {str(e)}"
                self.logger.log(error_msg)
                
                if on_complete:
                    on_complete(False, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=rename_thread, daemon=True).start()
    
    def get_file_content(self, remote_path, on_complete=None):
        """
        Get content of a text file
        
        Args:
            remote_path: Path to the remote file
            on_complete: Callback function(success, content, error_message)
        """
        def get_content_thread():
            normalized_remote_path = remote_path.replace('\\', '/') # Ensure forward slashes
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, None, "Could not establish SFTP connection")
                return
            
            try:
                # Create a StringIO object to store file content
                with sftp.open(normalized_remote_path, 'r') as f:
                    content = f.read().decode('utf-8', errors='replace')
                
                self.logger.log(f"Read content from {normalized_remote_path}")
                
                if on_complete:
                    on_complete(True, content, None)
            
            except Exception as e:
                error_msg = f"Error reading file {normalized_remote_path}: {str(e)}"
                self.logger.log(error_msg)
                
                if on_complete:
                    on_complete(False, None, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=get_content_thread, daemon=True).start()
    
    def save_file_content(self, remote_path, content, on_complete=None):
        """
        Save content to a text file
        
        Args:
            remote_path: Path to the remote file
            content: Text content to save
            on_complete: Callback function(success, error_message)
        """
        def save_content_thread():
            normalized_remote_path = remote_path.replace('\\', '/') # Ensure forward slashes
            sftp = self.ssh_client.get_sftp_client()
            if not sftp:
                if on_complete:
                    on_complete(False, "Could not establish SFTP connection")
                return
            
            try:
                # Write content to file
                with sftp.open(normalized_remote_path, 'wb') as f:
                    f.write(content.encode('utf-8'))
                
                self.logger.log(f"Saved content to {normalized_remote_path}")
                
                if on_complete:
                    on_complete(True, None)
            
            except Exception as e:
                error_msg = f"Error saving file {normalized_remote_path}: {str(e)}"
                self.logger.log(error_msg)
                
                if on_complete:
                    on_complete(False, error_msg)
        
        # Run in a separate thread
        threading.Thread(target=save_content_thread, daemon=True).start()
    
    def _count_dir_files(self, sftp, remote_dir, files_list, dirs_list, local_base_dir, rel_path):
        """
        Recursively count files in a directory for download
        
        Args:
            sftp: SFTP client
            remote_dir: Remote directory path
            files_list: List to add files to
            dirs_list: List to add directories to
            local_base_dir: Base local directory
            rel_path: Relative path from base directory (uses POSIX separators initially)
        """
        self.logger.log(f"SFTP _count_dir_files: ENTER remote_dir='{remote_dir}', local_base_dir='{local_base_dir}', rel_path='{rel_path}'")
        remote_dir = remote_dir.replace('\\', '/') # Ensure remote_dir uses forward slashes
        try:
            # Convert all paths to use correct OS-specific separators
            clean_rel_path = rel_path.replace('/', os.sep)
            local_dir_path = os.path.normpath(os.path.join(local_base_dir, clean_rel_path))
            dirs_list.append(local_dir_path)
            
            # List files in directory
            dir_items = sftp.listdir_attr(remote_dir)
            self.logger.log(f"SFTP _count_dir_files: Found {len(dir_items)} items in '{remote_dir}'")
            
            for item in dir_items:
                self.logger.log(f"SFTP _count_dir_files: Processing item '{item.filename}' in '{remote_dir}'. Mode: {item.st_mode}")
                # Build remote path with forward slashes (Unix style)
                remote_path = posixpath.join(remote_dir, item.filename)
                
                # Build relative path (Unix style first)
                unix_item_rel_path = posixpath.join(rel_path, item.filename)
                
                # Convert to OS-specific path for local use
                clean_item_rel_path = unix_item_rel_path.replace('/', os.sep)
                local_path = os.path.normpath(os.path.join(local_base_dir, clean_item_rel_path))
                
                if stat.S_ISDIR(item.st_mode):
                    # Recursively process subdirectory (pass Unix-style relative path)
                    self.logger.log(f"SFTP _count_dir_files: Item '{item.filename}' is a DIRECTORY. Recursing with remote_item_path='{remote_path}', new rel_path='{unix_item_rel_path}'")
                    self._count_dir_files(sftp, remote_path, files_list, dirs_list, 
                                         local_base_dir, unix_item_rel_path)
                else:
                    # Add file to download list
                    files_list.append({
                        'remote_path': remote_path,
                        'local_path': local_path,  # This is now OS-specific
                        'name': unix_item_rel_path  # Used for progress display, POSIX style is fine here
                    })
                    self.logger.log(f"SFTP _count_dir_files: Item '{item.filename}' is a FILE. Added to files_list. Remote='{remote_path}', Local='{local_path}', NameForProgress='{unix_item_rel_path}'")
        
        except Exception as e:
            self.logger.log(f"Error processing directory {remote_dir}: {str(e)}")
    
    def _delete_directory_recursive(self, sftp, remote_dir):
        """
        Recursively delete a directory and its contents
        
        Args:
            sftp: SFTP client
            remote_dir: Remote directory path
        """
        try:
            # List items in directory
            dir_items = sftp.listdir(remote_dir)
            
            for item_name in dir_items:
                item_path = posixpath.join(remote_dir, item_name)
                
                try:
                    # Check if it's a directory
                    if stat.S_ISDIR(sftp.stat(item_path).st_mode):
                        # Recursively delete subdirectory
                        self._delete_directory_recursive(sftp, item_path)
                    else:
                        # Delete file
                        sftp.remove(item_path)
                except Exception as e:
                    self.logger.log(f"Error deleting {item_path}: {str(e)}")
            
            # Delete the now-empty directory
            sftp.rmdir(remote_dir)
        
        except Exception as e:
            self.logger.log(f"Error deleting directory {remote_dir}: {str(e)}")
            raise
    
    def _format_permissions(self, mode):
        """Format file permissions as a string (like ls -l)"""
        perms = ['---', '--x', '-w-', '-wx', 'r--', 'r-x', 'rw-', 'rwx']
        perm_str = ''
        
        # File type
        if stat.S_ISDIR(mode):
            perm_str += 'd'
        elif stat.S_ISLNK(mode):
            perm_str += 'l'
        else:
            perm_str += '-'
        
        # User permissions
        perm_str += perms[(mode >> 6) & 0o7]
        # Group permissions
        perm_str += perms[(mode >> 3) & 0o7]
        # Other permissions
        perm_str += perms[mode & 0o7]
        
        return perm_str
    
    def _download_progress(self, transferred, total, filename, remote_path, local_path, callback=None):
        """Handle download progress updates"""
        if total == 0:  # Avoid division by zero
            percent = 100
        else:
            percent = (transferred / total) * 100
        
        status_msg = f"Downloading {filename}: {transferred}/{total} bytes ({percent:.1f}%)"
        
        if self.on_status_change:
            self.on_status_change(status_msg)
        
        if callback:
            callback(filename, transferred, total, percent)
    
    def _upload_progress(self, transferred, total, filename, remote_path, local_path, callback=None):
        """Handle upload progress updates"""
        if total == 0:  # Avoid division by zero
            percent = 100
        else:
            percent = (transferred / total) * 100
        
        status_msg = f"Uploading {filename}: {transferred}/{total} bytes ({percent:.1f}%)"
        
        if self.on_status_change:
            self.on_status_change(status_msg)
        
        if callback:
            callback(filename, transferred, total, percent)