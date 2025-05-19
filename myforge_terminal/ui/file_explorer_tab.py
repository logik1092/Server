"""
File: myforge_terminal/ui/file_explorer_tab.py
Description: File Explorer Tab Module - File management functionality

Structure:
  Classes:
    FileExplorerTab:
      Description: Initialize file explorer tab
      - __init__(self, notebook, ssh_client, sftp_ops, config, logger, theme_manager)
      - refresh_view(self)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import threading
import time

from utils.ui_utils import ContextMenu, ProgressDialog, FileEditDialog

class FileExplorerTab:
    def __init__(self, notebook, ssh_client, sftp_ops, config, logger, theme_manager):
        """Initialize file explorer tab"""
        self.notebook = notebook
        self.ssh_client = ssh_client
        self.sftp_ops = sftp_ops
        self.config = config
        self.logger = logger
        self.theme_manager = theme_manager
        
        # Create frame for file explorer tab
        self.frame = tk.Frame(notebook, bg=theme_manager.bg_color)
        
        # Set default path
        self.current_path = "/var/www/myforge.ai"
        
        # File selection state
        self.selected_items = []
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up file explorer UI"""
        # Path navigation frame
        self._setup_path_navigation()
        
        # Main explorer frame
        self._setup_explorer_frame()
        
        # Action buttons
        self._setup_action_buttons()
    
    def _setup_path_navigation(self):
        """Set up path navigation components"""
        nav_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Current path label
        tk.Label(nav_frame, text="Path:", bg=self.theme_manager.bg_color, 
                fg=self.theme_manager.fg_color).pack(side=tk.LEFT, padx=5)
        
        # Path entry with editable text
        self.path_var = tk.StringVar(value=self.current_path)
        self.path_entry = tk.Entry(
            nav_frame, textvariable=self.path_var, 
            bg="#2d2d2d", fg=self.theme_manager.fg_color
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind("<Return>", self._on_path_changed)
        
        # Navigate button
        ttk.Button(nav_frame, text="Go", command=self._on_path_changed).pack(side=tk.LEFT, padx=5)
        
        # Home button
        ttk.Button(nav_frame, text="Home", 
                  command=lambda: self._navigate_to_path("/home")).pack(side=tk.LEFT, padx=5)
        
        # Website button
        ttk.Button(nav_frame, text="Website", 
                  command=lambda: self._navigate_to_path("/var/www/myforge.ai")).pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        ttk.Button(nav_frame, text="↻", width=3, 
                  command=self.refresh_view).pack(side=tk.RIGHT, padx=5)
    
    def _setup_explorer_frame(self):
        """Set up the main file explorer frame"""
        explorer_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        explorer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for file listing
        self._setup_file_treeview(explorer_frame)
        
        # Create details panel
        self._setup_details_panel(explorer_frame)
    
    def _setup_file_treeview(self, parent_frame):
        """Set up file listing treeview"""
        # Left side for file tree
        tree_frame = tk.Frame(parent_frame, bg=self.theme_manager.bg_color)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbars
        columns = ("name", "size", "type", "modified", "permissions")
        self.file_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", 
            selectmode="extended"
        )
        
        # Define column headings
        self.file_tree.heading("name", text="Name")
        self.file_tree.heading("size", text="Size")
        self.file_tree.heading("type", text="Type")
        self.file_tree.heading("modified", text="Modified")
        self.file_tree.heading("permissions", text="Permissions")
        
        # Configure column widths
        self.file_tree.column("name", width=200, stretch=True)
        self.file_tree.column("size", width=80, anchor=tk.E, stretch=False)
        self.file_tree.column("type", width=80, stretch=False)
        self.file_tree.column("modified", width=140, stretch=False)
        self.file_tree.column("permissions", width=100, stretch=False)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack scrollbars and treeview
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.file_tree.bind("<Double-1>", self._on_item_double_click)
        self.file_tree.bind("<Button-3>", self._show_context_menu)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        
        # Create context menu for tree
        self._create_context_menu()
    
    def _setup_details_panel(self, parent_frame):
        """Set up file details panel"""
        # Right side for details
        details_frame = tk.LabelFrame(
            parent_frame, text="Details", 
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
            width=250
        )
        details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        details_frame.pack_propagate(False)  # Prevent shrinking
        
        # Details content
        self.details_name = tk.StringVar(value="")
        self.details_path = tk.StringVar(value="")
        self.details_size = tk.StringVar(value="")
        self.details_type = tk.StringVar(value="")
        self.details_modified = tk.StringVar(value="")
        self.details_perms = tk.StringVar(value="")
        
        # Details labels
        detail_labels = [
            ("Name:", self.details_name),
            ("Path:", self.details_path),
            ("Size:", self.details_size),
            ("Type:", self.details_type),
            ("Modified:", self.details_modified),
            ("Permissions:", self.details_perms)
        ]
        
        for i, (label_text, var) in enumerate(detail_labels):
            label_frame = tk.Frame(details_frame, bg=self.theme_manager.bg_color)
            label_frame.pack(fill=tk.X, padx=5, pady=2, anchor=tk.W)
            
            tk.Label(
                label_frame, text=label_text, width=10, anchor=tk.W,
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
            ).pack(side=tk.LEFT)
            
            detail_label = tk.Label(
                label_frame, textvariable=var, anchor=tk.W,
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
            )
            detail_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Preview frame (future enhancement)
        preview_frame = tk.LabelFrame(
            details_frame, text="Preview", 
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_label = tk.Label(
            preview_frame, text="No preview available",
            bg="#2d2d2d", fg=self.theme_manager.fg_color,
            wraplength=230, justify=tk.LEFT
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _setup_action_buttons(self):
        """Set up action buttons for file operations"""
        btn_frame = tk.Frame(self.frame, bg=self.theme_manager.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left side buttons
        ttk.Button(
            btn_frame, text="Upload File", 
            command=self._upload_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="New Folder", 
            command=self._create_new_folder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="Edit Selected", 
            command=self._edit_selected_file
        ).pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        ttk.Button(
            btn_frame, text="Download Selected", 
            command=self._download_selected
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame, text="Delete Selected", 
            command=self._delete_selected
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_context_menu(self):
        """Create context menu for file tree"""
        self.context_menu = tk.Menu(self.file_tree, tearoff=0, 
                                  bg="#2d2d2d", fg=self.theme_manager.fg_color)
        
        self.context_menu.add_command(label="Download", command=self._download_selected)
        self.context_menu.add_command(label="Upload Here", command=self._upload_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit", command=self._edit_selected_file)
        self.context_menu.add_command(label="Rename", command=self._rename_selected)
        self.context_menu.add_command(label="Delete", command=self._delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="New Folder", command=self._create_new_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh", command=self.refresh_view)
    
    def refresh_view(self):
        """Refresh the file listing"""
        if not self.ssh_client.connected:
            messagebox.showinfo("Not Connected", 
                             "Please connect to a server first.")
            return
        
        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Clear details
        self._clear_details()
        
        # Start directory listing
        self.sftp_ops.list_directory(
            self.current_path, 
            on_complete=self._on_directory_listed
        )
    
    def _on_directory_listed(self, success, items, error_message):
        """Handle directory listing completion"""
        if not success:
            messagebox.showerror("Error", f"Failed to list directory: {error_message}")
            return
        
        # Update path
        self.current_path = self.sftp_ops.current_remote_path
        self.path_var.set(self.current_path)
        
        # Add items to tree
        for item in items:
            # Format size for display
            if item['type'] == 'directory':
                size_str = "<DIR>"
            else:
                size_str = self._format_size(item['size'])
            
            # Insert into tree
            self.file_tree.insert(
                "", "end",
                values=(
                    item['name'],
                    size_str,
                    item['type'],
                    item['modified'],
                    item['permissions']
                ),
                tags=(item['type'], "parent" if item.get('is_parent', False) else "")
            )
        
        # Configure tags
        self.file_tree.tag_configure('directory', foreground='#77ccff')
        self.file_tree.tag_configure('file', foreground=self.theme_manager.fg_color)
        self.file_tree.tag_configure('link', foreground='#ffaa77')
        self.file_tree.tag_configure('parent', foreground='#aaaaaa')
    
    def _on_item_double_click(self, event):
        """Handle double-click on tree item"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_values = self.file_tree.item(item_id, "values")
        
        if not item_values:
            return
        
        name, size, item_type = item_values[0], item_values[1], item_values[2]
        
        if item_type == 'directory':
            # Navigate to directory
            if name == '..':
                # Go up one level
                self._navigate_to_path(os.path.dirname(self.current_path))
            else:
                # Go into directory
                new_path = os.path.join(self.current_path, name)
                self._navigate_to_path(new_path)
        else:
            # Open file for editing
            self._edit_selected_file()
    
    def _on_selection_changed(self, event):
        """Handle selection change in tree"""
        selection = self.file_tree.selection()
        if not selection:
            self._clear_details()
            self.selected_items = []
            return
        
        # Get selected items
        self.selected_items = []
        for item_id in selection:
            item_values = self.file_tree.item(item_id, "values")
            if not item_values:
                continue
            
            name, size_str, item_type, modified, perms = item_values
            path = os.path.join(self.current_path, name) if name != '..' else os.path.dirname(self.current_path)
            
            # Convert size string back to number
            if size_str == "<DIR>":
                size = 0
            else:
                try:
                    if "KB" in size_str:
                        size = float(size_str.replace("KB", "").strip()) * 1024
                    elif "MB" in size_str:
                        size = float(size_str.replace("MB", "").strip()) * 1024 * 1024
                    elif "GB" in size_str:
                        size = float(size_str.replace("GB", "").strip()) * 1024 * 1024 * 1024
                    else:
                        size = float(size_str.replace("B", "").strip())
                except ValueError:
                    size = 0
            
            self.selected_items.append({
                'name': name,
                'path': path,
                'type': item_type,
                'size': size,
                'modified': modified,
                'permissions': perms,
                'is_parent': name == '..'
            })
        
        # Update details for first selected item
        if self.selected_items:
            self._update_details(self.selected_items[0])
    
    def _update_details(self, item):
        """Update details panel with item information"""
        self.details_name.set(item['name'])
        self.details_path.set(item['path'])
        
        if item['type'] == 'directory':
            self.details_size.set("<Directory>")
        else:
            self.details_size.set(self._format_size(item['size']))
        
        self.details_type.set(item['type'].capitalize())
        self.details_modified.set(item['modified'])
        self.details_perms.set(item['permissions'])
        
        # Update preview (for text files)
        if item['type'] == 'file' and self._is_text_file(item['name']):
            # Get file preview
            self._show_file_preview(item['path'])
        else:
            self.preview_label.config(text="No preview available")
    
    def _clear_details(self):
        """Clear details panel"""
        self.details_name.set("")
        self.details_path.set("")
        self.details_size.set("")
        self.details_type.set("")
        self.details_modified.set("")
        self.details_perms.set("")
        self.preview_label.config(text="No preview available")
    
    def _show_file_preview(self, path, max_size=1024*10):
        """Show a preview of the file content"""
        if not self.ssh_client.connected:
            return
        
        def on_content_loaded(success, content, error):
            if success and content:
                # Limit preview size
                preview_text = content[:max_size]
                if len(content) > max_size:
                    preview_text += "\n...(file truncated)..."
                self.preview_label.config(text=preview_text)
            else:
                self.preview_label.config(text="Preview failed to load")
        
        # Get file content
        self.sftp_ops.get_file_content(path, on_complete=on_content_loaded)
    
    def _navigate_to_path(self, path):
        """Navigate to a different directory"""
        if not self.ssh_client.connected:
            return
        
        # Normalize path separators for SFTP
        path = path.replace("\\", "/")
        
        # Update current path and refresh view
        self.current_path = path
        self.path_var.set(path)
        self.refresh_view()
    
    def _on_path_changed(self, event=None):
        """Handle path entry change"""
        new_path = self.path_var.get()
        if new_path and new_path != self.current_path:
            self._navigate_to_path(new_path)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select item under cursor if not already selected
        item = self.file_tree.identify('item', event.x, event.y)
        if item and item not in self.file_tree.selection():
            self.file_tree.selection_set(item)
        
        # Show menu
        if self.file_tree.selection():
            self.context_menu.post(event.x_root, event.y_root)
    
    def _download_selected(self):
        """Download selected files and directories"""
        if not self.ssh_client.connected or not self.selected_items:
            return
        
        # Filter out parent directory
        items_to_download = [item for item in self.selected_items 
                            if not item.get('is_parent', False)]
        
        if not items_to_download:
            messagebox.showinfo("No Selection", 
                             "Please select files or directories to download.")
            return
        
        # Ask for download location
        download_dir = filedialog.askdirectory(
            title="Select Download Location"
        )
        
        if not download_dir:
            return
        
        # Start download with progress dialog
        progress_dialog = ProgressDialog(
            self.frame, 
            "Downloading Files",
            "Preparing to download...",
            self.theme_manager
        )
        
        def on_progress(filename, transferred, total, percent):
            progress_dialog.update_progress(
                f"Downloading {filename}",
                percent / 100.0
            )
        
        def on_complete(success, downloaded, failed, error):
            progress_dialog.close()
            
            if success:
                messagebox.showinfo(
                    "Download Complete",
                    f"Downloaded {downloaded} files successfully."
                )
            else:
                messagebox.showerror(
                    "Download Failed",
                    f"Download failed: {error}\n"
                    f"Files downloaded: {downloaded}, Files failed: {failed}"
                )
        
        # Start download
        self.sftp_ops.download_files(
            items_to_download,
            download_dir,
            on_progress=on_progress,
            on_complete=on_complete
        )
    
    def _upload_files(self):
        """Upload files to current directory"""
        if not self.ssh_client.connected:
            messagebox.showinfo("Not Connected", 
                             "Please connect to a server first.")
            return
        
        # Ask for files to upload
        files = filedialog.askopenfilenames(
            title="Select Files to Upload"
        )
        
        if not files:
            return
        
        # Ask for overwrite confirmation if needed
        overwrite = messagebox.askyesno(
            "Confirm Upload",
            "Overwrite existing files with the same name?",
            default=messagebox.NO
        )
        
        # Start upload with progress dialog
        progress_dialog = ProgressDialog(
            self.frame, 
            "Uploading Files",
            "Preparing to upload...",
            self.theme_manager
        )
        
        def on_progress(filename, transferred, total, percent):
            progress_dialog.update_progress(
                f"Uploading {filename}",
                percent / 100.0
            )
        
        def on_complete(success, uploaded, failed, error):
            progress_dialog.close()
            
            if success:
                messagebox.showinfo(
                    "Upload Complete",
                    f"Uploaded {uploaded} files successfully."
                )
                # Refresh view
                self.refresh_view()
            else:
                messagebox.showerror(
                    "Upload Failed",
                    f"Upload failed: {error}\n"
                    f"Files uploaded: {uploaded}, Files failed: {failed}"
                )
        
        # Start upload
        self.sftp_ops.upload_files(
            files,
            self.current_path,
            overwrite=overwrite,
            on_progress=on_progress,
            on_complete=on_complete
        )
    
    def _create_new_folder(self):
        """Create a new folder in the current directory"""
        if not self.ssh_client.connected:
            return
        
        # Ask for folder name
        folder_name = simpledialog.askstring(
            "New Folder",
            "Enter name for new folder:",
            parent=self.frame
        )
        
        if not folder_name:
            return
        
        # Create folder
        self.sftp_ops.create_directory(
            self.current_path,
            folder_name,
            on_complete=lambda success, error: self._on_create_folder_complete(
                success, error, folder_name
            )
        )
    
    def _on_create_folder_complete(self, success, error, folder_name):
        """Handle folder creation completion"""
        if success:
            messagebox.showinfo(
                "Folder Created",
                f"Folder '{folder_name}' created successfully."
            )
            # Refresh view
            self.refresh_view()
        else:
            messagebox.showerror(
                "Error",
                f"Failed to create folder: {error}"
            )
    
    def _delete_selected(self):
        """Delete selected files and directories"""
        if not self.ssh_client.connected or not self.selected_items:
            return
        
        # Filter out parent directory
        items_to_delete = [item for item in self.selected_items 
                          if not item.get('is_parent', False)]
        
        if not items_to_delete:
            messagebox.showinfo("No Selection", 
                             "Please select files or directories to delete.")
            return
        
        # Confirm deletion
        item_names = [item['name'] for item in items_to_delete]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete {len(items_to_delete)} item(s)?\n\n"
            f"{', '.join(item_names[:5])}"
            f"{' and more...' if len(item_names) > 5 else ''}"
        ):
            return
        
        # Delete items one by one
        for item in items_to_delete:
            self.sftp_ops.delete_item(
                item,
                on_complete=lambda success, error, item=item: self._on_delete_complete(
                    success, error, item
                )
            )
    
    def _on_delete_complete(self, success, error, item):
        """Handle item deletion completion"""
        if not success:
            messagebox.showerror(
                "Delete Failed",
                f"Failed to delete {item['name']}: {error}"
            )
    
    def _rename_selected(self):
        """Rename selected file or directory"""
        if not self.ssh_client.connected or not self.selected_items:
            return
        
        # Get selected item (only single selection supported for rename)
        item = self.selected_items[0]
        
        if item.get('is_parent', False):
            messagebox.showinfo("Cannot Rename", 
                             "Cannot rename parent directory.")
            return
        
        # Ask for new name
        new_name = simpledialog.askstring(
            "Rename",
            f"Enter new name for '{item['name']}':",
            initialvalue=item['name'],
            parent=self.frame
        )
        
        if not new_name or new_name == item['name']:
            return
        
        # Rename item
        self.sftp_ops.rename_item(
            item,
            new_name,
            on_complete=lambda success, error: self._on_rename_complete(
                success, error, item['name'], new_name
            )
        )
    
    def _on_rename_complete(self, success, error, old_name, new_name):
        """Handle item rename completion"""
        if success:
            messagebox.showinfo(
                "Rename Complete",
                f"Renamed '{old_name}' to '{new_name}' successfully."
            )
            # Refresh view
            self.refresh_view()
        else:
            messagebox.showerror(
                "Rename Failed",
                f"Failed to rename '{old_name}': {error}"
            )
    
    def _edit_selected_file(self):
        """Edit selected text file"""
        if not self.ssh_client.connected or not self.selected_items:
            return
        
        # Get selected item
        item = self.selected_items[0]
        
        if item['type'] != 'file' or not self._is_text_file(item['name']):
            messagebox.showinfo("Cannot Edit", 
                             "Can only edit text files.")
            return
        
        # Get file content
        self.sftp_ops.get_file_content(
            item['path'],
            on_complete=lambda success, content, error: self._on_file_content_loaded(
                success, content, error, item
            )
        )
    
    def _on_file_content_loaded(self, success, content, error, item):
        """Handle file content loading for editing"""
        if not success:
            messagebox.showerror(
                "Error",
                f"Failed to load file content: {error}"
            )
            return
        
        # Open editor dialog
        editor = FileEditDialog(
            self.frame,
            item['name'],
            content,
            self.theme_manager,
            on_save=lambda new_content: self._save_edited_file(
                item['path'], new_content
            )
        )
    
    def _save_edited_file(self, path, content):
        """Save edited file content"""
        self.sftp_ops.save_file_content(
            path,
            content,
            on_complete=lambda success, error: self._on_file_save_complete(
                success, error, path
            )
        )
    
    def _on_file_save_complete(self, success, error, path):
        """Handle file save completion"""
        if success:
            messagebox.showinfo(
                "Save Complete",
                f"File saved successfully."
            )
            # Update preview if the file is selected
            if self.selected_items and self.selected_items[0]['path'] == path:
                self._show_file_preview(path)
        else:
            messagebox.showerror(
                "Save Failed",
                f"Failed to save file: {error}"
            )
    
    def _format_size(self, size_bytes):
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                if unit == 'B':
                    return f"{size_bytes} {unit}"
                else:
                    return f"{size_bytes/1024:.1f} {unit}"
            size_bytes /= 1024
    
    def _is_text_file(self, filename):
        """Check if a file is likely a text file based on extension"""
        text_extensions = [
            '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md',
            '.ini', '.conf', '.cfg', '.log', '.sh', '.bash', '.php', '.c',
            '.cpp', '.h', '.java', '.yaml', '.yml', '.toml', '.csv', '.lua'
        ]
        
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in text_extensions)