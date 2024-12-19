import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime

from ssh_file_system_api import SSHFileSystemApi


class FileExplorerGUI:
    def __init__(self, master):
        self.master = master
        self.ssh_api: SSHFileSystemApi = None
        self.create_connection_prompt()

    def initialize_theme(self):
        self.master.title("Modern Dark File Explorer")
        self.master.geometry("1024x600")

        # Create a style object
        self.style = ttk.Style()

        # Create a new dark theme based on 'clam' or 'default'
        # We use 'clam' as a base since it's quite neutral.
        try:
            self.style.theme_create(
                "darkmode",
                parent="clam",
                settings={
                    "TFrame": {
                        "configure": {"background": "#2b2b2b"}  # Dark grey background
                    },
                    "TLabel": {
                        "configure": {
                            "background": "#2b2b2b",
                            "foreground": "#ffffff",
                            "font": ("Segoe UI", 10),
                        }
                    },
                    "TButton": {
                        "configure": {
                            "background": "#3c3f41",
                            "foreground": "#ffffff",
                            "font": ("Segoe UI", 10),
                            "padding": 5,
                        },
                        "map": {"background": [("active", "#4f5355")]},
                    },
                    "TEntry": {
                        "configure": {
                            "fieldbackground": "#3c3f41",
                            "foreground": "#ffffff",
                            "insertcolor": "#ffffff",
                            "font": ("Segoe UI", 10),
                        }
                    },
                    "Treeview": {
                        "configure": {
                            "background": "#3c3f41",
                            "foreground": "#ffffff",
                            "fieldbackground": "#3c3f41",
                            "font": ("Segoe UI", 10),
                            "rowheight": 24,
                        },
                        "map": {
                            "background": [("selected", "#616161")],
                            "foreground": [("selected", "#ffffff")],
                        },
                    },
                    "Vertical.TScrollbar": {
                        "configure": {"background": "#3c3f41", "troughcolor": "#2b2b2b"}
                    },
                    "Horizontal.TScrollbar": {
                        "configure": {"background": "#3c3f41", "troughcolor": "#2b2b2b"}
                    },
                },
            )
        except tk.TclError:
            # If the theme already exists for some reason, pass
            pass

        self.style.theme_use("darkmode")

    def initialize_gui(self):
        # Main frames: Left (tree), Right (details)
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)

        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack(side="left", fill="y")

        self.details_frame = ttk.Frame(self.main_frame)
        self.details_frame.pack(side="right", fill="both", expand=True)

        # Toolbar
        self.toolbar = ttk.Frame(self.details_frame)
        self.toolbar.pack(side="top", fill="x", pady=5, padx=5)

        self.path_var = tk.StringVar(value=self.ssh_api.pwd())
        self.path_entry = ttk.Entry(self.toolbar, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.go_button = ttk.Button(
            self.toolbar, text="Go", command=self.change_directory
        )
        self.go_button.pack(side="left", padx=(0, 5))

        self.refresh_button = ttk.Button(
            self.toolbar, text="Refresh", command=self.refresh
        )
        self.refresh_button.pack(side="left")

        # Directory Tree View
        self.dir_tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.dir_tree.pack(fill="y", expand=True, padx=5, pady=5)

        self.dir_scrollbar = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.dir_tree.yview
        )
        self.dir_scrollbar.pack(side="right", fill="y")
        self.dir_tree.configure(yscrollcommand=self.dir_scrollbar.set)

        self.dir_tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.dir_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # File List View
        columns = ("Name", "Size", "Type", "Modified")
        self.file_list = ttk.Treeview(
            self.details_frame, columns=columns, show="headings"
        )
        for col in columns:
            self.file_list.heading(col, text=col)
            self.file_list.column(col, anchor="w", width=150)

        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.file_scrollbar_y = ttk.Scrollbar(
            self.details_frame, orient="vertical", command=self.file_list.yview
        )
        self.file_scrollbar_y.pack(side="right", fill="y")
        self.file_list.configure(yscrollcommand=self.file_scrollbar_y.set)

        self.file_scrollbar_x = ttk.Scrollbar(
            self.details_frame, orient="horizontal", command=self.file_list.xview
        )
        self.file_scrollbar_x.pack(side="bottom", fill="x")
        self.file_list.configure(xscrollcommand=self.file_scrollbar_x.set)

        self.populate_tree_root()
        self.refresh()

    def create_connection_prompt(self):
        prompt = tk.Toplevel(self.master)
        prompt.title("Connect to Server")
        prompt.grab_set()  # Make the prompt modal

        ttk.Label(prompt, text="IP Address:").grid(row=0, column=0, padx=5, pady=5)
        ip_entry = ttk.Entry(prompt)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(prompt, text="Port:").grid(row=1, column=0, padx=5, pady=5)
        port_entry = ttk.Entry(prompt)
        port_entry.grid(row=1, column=1, padx=5, pady=5)
        port_entry.insert(0, "22")

        ttk.Label(prompt, text="Username:").grid(row=2, column=0, padx=5, pady=5)
        username_entry = ttk.Entry(prompt)
        username_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(prompt, text="Password:").grid(row=3, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(prompt, show="*")
        password_entry.grid(row=3, column=1, padx=5, pady=5)

        def connect():
            ip = ip_entry.get()
            port = int(port_entry.get())
            username = username_entry.get()
            password = password_entry.get()
            try:
                self.ssh_api = SSHFileSystemApi(ip, port, username, password)
                prompt.grab_release()  # Release the modal property
                prompt.destroy()
                self.initialize_theme()
                self.initialize_gui()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))

        connect_button = ttk.Button(prompt, text="Connect", command=connect)
        connect_button.grid(row=4, column=0, columnspan=2, pady=10)

        prompt.wait_window()  # Wait for the prompt to close before continuing

    def populate_tree_root(self):
        # Populate the root directories (in this example, just "/")
        root_node = self.dir_tree.insert("", "end", text="/", open=True, values=("/"))
        self.populate_tree(root_node, "/")

    def populate_tree(self, parent_node, path):
        try:
            dirs = self.ssh_api.list_directory_contents(path)
            # Filter directories only, for the tree
            for d in dirs:
                full_path = self.ssh_api.resolve_path(os.path.join(path, d))
                if self.fs_api.is_directory(full_path):
                    node = self.dir_tree.insert(
                        parent_node, "end", text=d, values=(full_path,)
                    )
                    # Add a dummy child so we can expand this node later
                    self.dir_tree.insert(node, "end", text="...")
        except Exception as e:
            print(f"Error populating tree: {e}")

    def on_tree_open(self, event):
        node = self.dir_tree.selection()[0]
        path = self.dir_tree.item(node, "values")[0]

        # Clear existing children (the dummy one)
        self.dir_tree.delete(*self.dir_tree.get_children(node))
        # Repopulate
        self.populate_tree(node, path)

    def on_tree_select(self, event):
        node = self.dir_tree.selection()[0]
        path = self.dir_tree.item(node, "values")[0]
        self.path_var.set(path)
        self.refresh()

    def change_directory(self):
        new_path = self.path_var.get()
        try:
            self.ssh_api.change_directory(new_path)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        # Clear the file list
        for row in self.file_list.get_children():
            self.file_list.delete(row)

        current_path = self.path_var.get()
        try:
            contents = self.ssh_api.list_directory_contents(current_path)
            for item in contents:
                meta = self.ssh_api.get_file_metadata(os.path.join(current_path, item))
                size_str = self._format_size(meta.file_size)
                file_type = "Directory" if meta.is_directory else "File"
                mod_time = (
                    meta.modification_date.strftime("%Y-%m-%d %H:%M:%S")
                    if meta.modification_date
                    else ""
                )
                self.file_list.insert(
                    "", "end", values=(item, size_str, file_type, mod_time)
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _format_size(self, size_bytes):
        # Simple human-readable format
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"


if __name__ == "__main__":
    root = tk.Tk()
    explorer = FileExplorerGUI(root)

    root.mainloop()
