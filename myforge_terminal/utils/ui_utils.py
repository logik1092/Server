"""
File: myforge_terminal/utils/ui_utils.py
Description: UI Utilities Module - Common UI components and helpers

Structure:
  Classes:
    ThemeManager:
      Description: Manage application themes
      - __init__(self, root, config)
      - apply_theme(self, theme_name)
    ContextMenu:
      Description: Contextual right-click menu
      - __init__(self, widget, theme_manager)
      - add_command(self, label, command)
      - add_separator(self)
    ProgressDialog:
      Description: Dialog with progress bar
      - __init__(self, parent, title, message, theme_manager)
      - update_progress(self, message, progress)
      - close(self)
    FileEditDialog:
      Description: Dialog for editing files
      - __init__(self, parent, filename, content, theme_manager, on_save=None)
    InputDialog(simpledialog.Dialog):
      Description: Custom input dialog with multiple fields
      - __init__(self, parent, title, fields, theme_manager)
      - body(self, master)
      - apply(self)
  Functions:
    - center_window(window, parent=None)
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext
import os

class ThemeManager:
    """Manage application themes"""
    
    def __init__(self, root, config):
        """Initialize theme manager"""
        self.root = root
        self.config = config
        
        # Set default colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#3a7ebf"
        self.highlight_color = "#5a5a5a"
        self.selection_color = "#215d9c"
        
        # Initialize theme
        self.apply_theme(config.get("theme", "dark"))
    
    def apply_theme(self, theme_name):
        """Apply theme to all widgets"""
        if theme_name == "dark":
            self.bg_color = "#1e1e1e"
            self.fg_color = "#e0e0e0"
            self.accent_color = "#3a7ebf"
            self.highlight_color = "#5a5a5a"
            self.selection_color = "#215d9c"
            self.text_bg = "#2d2d2d"
            self.text_insert_bg = "#e0e0e0"  # Bright cursor for dark background
        else:  # Light theme
            self.bg_color = "#f0f0f0"
            self.fg_color = "#202020"
            self.accent_color = "#0078d7"
            self.highlight_color = "#d0d0d0"
            self.selection_color = "#90c8f6"
            self.text_bg = "#ffffff"
            self.text_insert_bg = "#202020"  # Dark cursor for light background
        
        # Configure ttk styles
        self._configure_styles()
        
        # Store theme in config
        self.config.set("theme", theme_name)
    
    def _configure_styles(self):
        """Configure ttk styles for the current theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for various widget states
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground=self.fg_color, padding=[10, 2])
        style.map("TNotebook.Tab", background=[("selected", self.accent_color)], 
                 foreground=[("selected", "#ffffff")])
        
        style.configure("TButton", background="#3a3a3a", foreground=self.fg_color, borderwidth=1)
        style.map("TButton", background=[("active", self.accent_color)], 
                foreground=[("active", "#ffffff")])
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("TEntry", fieldbackground="#2d2d2d", foreground=self.fg_color)
        
        # Progressbar
        style.configure("TProgressbar", background=self.accent_color, 
                       troughcolor="#2d2d2d", borderwidth=0)

class ContextMenu:
    """Contextual right-click menu"""
    
    def __init__(self, widget, theme_manager):
        """Initialize context menu for a widget"""
        self.widget = widget
        self.theme_manager = theme_manager
        
        # Create menu
        self.menu = tk.Menu(
            widget, tearoff=0,
            bg="#2d2d2d", fg=theme_manager.fg_color,
            activebackground=theme_manager.accent_color,
            activeforeground="#ffffff"
        )
        
        # Bind right-click
        widget.bind("<Button-3>", self._show_menu)
    
    def add_command(self, label, command):
        """Add command to menu"""
        self.menu.add_command(label=label, command=command)
    
    def add_separator(self):
        """Add separator to menu"""
        self.menu.add_separator()
    
    def _show_menu(self, event):
        """Show menu at cursor position"""
        self.menu.post(event.x_root, event.y_root)

class ProgressDialog:
    """Dialog with progress bar"""
    
    def __init__(self, parent, title, message, theme_manager):
        """Initialize progress dialog"""
        self.parent = parent
        self.theme_manager = theme_manager
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x120")
        self.dialog.configure(bg=theme_manager.bg_color)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center dialog
        self._center_window()
        
        # Message label
        self.message_var = tk.StringVar(value=message)
        tk.Label(
            self.dialog, textvariable=self.message_var,
            bg=theme_manager.bg_color, fg=theme_manager.fg_color,
            wraplength=380, justify=tk.LEFT
        ).pack(padx=10, pady=10, fill=tk.X)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.dialog, orient=tk.HORIZONTAL, length=380, mode='determinate'
        )
        self.progress_bar.pack(padx=10, pady=10, fill=tk.X)
        
        # Cancel button (optional)
        self.cancel_var = tk.BooleanVar(value=False)
        ttk.Button(
            self.dialog, text="Cancel",
            command=self._on_cancel
        ).pack(pady=5)
        
        # Update dialog
        self.dialog.update()
    
    def update_progress(self, message, progress):
        """Update progress and message"""
        self.message_var.set(message)
        self.progress_bar['value'] = progress * 100
        self.dialog.update()
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.cancel_var.set(True)
        self.dialog.destroy()
    
    def _on_close(self):
        """Handle dialog close"""
        self.cancel_var.set(True)
        self.dialog.destroy()
    
    def close(self):
        """Close the dialog"""
        if hasattr(self, 'dialog') and self.dialog.winfo_exists():
            self.dialog.destroy()
    
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

class FileEditDialog:
    """Dialog for editing files"""
    
    def __init__(self, parent, filename, content, theme_manager, on_save=None):
        """Initialize file edit dialog"""
        self.parent = parent
        self.theme_manager = theme_manager
        self.on_save = on_save
        self.filename = filename
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit: {filename}")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg=theme_manager.bg_color)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_window()
        
        # Setup UI
        self._setup_ui(content)
    
    def _setup_ui(self, content):
        """Set up dialog UI"""
        # File info
        tk.Label(
            self.dialog, text=f"Editing: {self.filename}",
            bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
        ).pack(pady=5)
        
        # Line numbers and text area frame
        edit_frame = tk.Frame(self.dialog, bg=self.theme_manager.bg_color)
        edit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create scrolled text area
        self.edit_area = scrolledtext.ScrolledText(
            edit_frame, wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#2d2d2d", fg=self.theme_manager.fg_color,
            insertbackground=self.theme_manager.fg_color
        )
        self.edit_area.pack(fill=tk.BOTH, expand=True)
        
        # Insert content
        self.edit_area.insert(tk.END, content)
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(
            edit_frame, orient=tk.HORIZONTAL,
            command=self.edit_area.xview
        )
        h_scrollbar.pack(fill=tk.X)
        self.edit_area.config(xscrollcommand=h_scrollbar.set)
        
        # Button frame
        btn_frame = tk.Frame(self.dialog, bg=self.theme_manager.bg_color)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, text="Save Changes",
            command=self._save
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame, text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=10)
        
        # Set focus to edit area
        self.edit_area.focus_set()
        
        # Bind keys
        self.dialog.bind("<Control-s>", self._save)
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
    
    def _save(self, event=None):
        """Save changes"""
        if messagebox.askyesno(
            "Confirm Save",
            f"Are you sure you want to save changes to\n{self.filename}?",
            parent=self.dialog
        ):
            # Get content
            content = self.edit_area.get(1.0, tk.END)
            
            # Call save callback
            if self.on_save:
                self.on_save(content)
            
            # Close dialog
            self.dialog.destroy()
    
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

class InputDialog(simpledialog.Dialog):
    """Custom input dialog with multiple fields"""
    
    def __init__(self, parent, title, fields, theme_manager):
        """
        Initialize input dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            fields: List of field dictionaries with keys:
                   - name: Field name
                   - label: Field label
                   - type: Field type (entry, password, text, checkbox)
                   - default: Default value
            theme_manager: Theme manager
        """
        self.fields = fields
        self.theme_manager = theme_manager
        self.result = None
        self.entries = {}
        
        super().__init__(parent, title)
    
    def body(self, master):
        """Create dialog body"""
        # Configure master
        master.configure(bg=self.theme_manager.bg_color)
        
        # Create entries for each field
        for i, field in enumerate(self.fields):
            label = tk.Label(
                master, text=field['label'],
                bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color
            )
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            
            field_type = field.get('type', 'entry')
            field_name = field['name']
            field_default = field.get('default', '')
            
            if field_type == 'entry':
                entry = tk.Entry(
                    master, bg="#2d2d2d", fg=self.theme_manager.fg_color,
                    insertbackground=self.theme_manager.fg_color
                )
                entry.insert(0, field_default)
            elif field_type == 'password':
                entry = tk.Entry(
                    master, show='*', bg="#2d2d2d", fg=self.theme_manager.fg_color,
                    insertbackground=self.theme_manager.fg_color
                )
                entry.insert(0, field_default)
            elif field_type == 'text':
                entry = scrolledtext.ScrolledText(
                    master, height=5, width=30, bg="#2d2d2d", fg=self.theme_manager.fg_color,
                    insertbackground=self.theme_manager.fg_color
                )
                entry.insert(tk.END, field_default)
            elif field_type == 'checkbox':
                var = tk.BooleanVar(value=field_default)
                entry = tk.Checkbutton(
                    master, variable=var,
                    bg=self.theme_manager.bg_color, fg=self.theme_manager.fg_color,
                    selectcolor="#2d2d2d",
                    activebackground=self.theme_manager.bg_color,
                    activeforeground=self.theme_manager.fg_color
                )
                entry.var = var
            
            entry.grid(row=i, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
            self.entries[field_name] = entry
        
        return list(self.entries.values())[0]  # Return first entry for focus
    
    def apply(self):
        """Process result when OK is clicked"""
        result = {}
        
        for field in self.fields:
            field_name = field['name']
            field_type = field.get('type', 'entry')
            entry = self.entries[field_name]
            
            if field_type == 'entry' or field_type == 'password':
                result[field_name] = entry.get()
            elif field_type == 'text':
                result[field_name] = entry.get(1.0, tk.END).strip()
            elif field_type == 'checkbox':
                result[field_name] = entry.var.get()
        
        self.result = result

def center_window(window, parent=None):
    """Center a window on the screen or parent"""
    window.withdraw()
    window.update_idletasks()
    
    width = window.winfo_width()
    height = window.winfo_height()
    
    if parent:
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    else:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
    
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.deiconify()