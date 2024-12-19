import tkinter as tk
from tkinter import ttk, messagebox
import sys

from ssh_file_system_api import SSHFileSystemApi
import threading

# For a nicer dark theme, we can use a dark background and custom styles.
# Alternatively, consider using customtkinter for an even better look.


class FileEditor(tk.Toplevel):
    def __init__(self, master, ssh_api, filepath, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.ssh_api = ssh_api
        self.filepath = filepath
        self.title(f"Editing: {filepath}")

        self.configure(bg="#2d2d2d")

        # A simple text widget for editing
        self.text = tk.Text(
            self, wrap="word", fg="#ffffff", bg="#3c3c3c", insertbackground="white"
        )
        self.text.pack(fill="both", expand=True)

        # Load file content
        try:
            content = self.ssh_api.get_file_content(filepath)
            self.text.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

        # A save button
        button_frame = tk.Frame(self, bg="#2d2d2d")
        button_frame.pack(side="bottom", fill="x", pady=5)

        save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save_file,
            bg="#444444",
            fg="white",
            highlightbackground="#2d2d2d",
        )
        save_button.pack(side="right", padx=10)

        cancel_button = tk.Button(
            button_frame,
            text="Close",
            command=self.destroy,
            bg="#444444",
            fg="white",
            highlightbackground="#2d2d2d",
        )
        cancel_button.pack(side="right", padx=10)

        self.run_in_thread(
            self.ssh_api.get_file_content, (filepath,), self.on_file_content_loaded
        )

    def on_file_content_loaded(self, content, error):
        if error:
            messagebox.showerror("Error", f"Failed to open file:\n{error}")
        else:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)

    def save_file(self):
        content = self.text.get("1.0", "end-1c")
        self.run_in_thread(
            self.ssh_api.write_file_content,
            (self.filepath, content),
            self.on_file_saved,
        )

    def on_file_saved(self, result, error):
        if error:
            messagebox.showerror("Error", f"Failed to save file:\n{error}")
        else:
            messagebox.showinfo("Saved", f"File {self.filepath} saved successfully.")

    def run_in_thread(self, func, args, callback):
        # Generic helper to run blocking SSH calls in a separate thread
        def worker():
            try:
                res = func(*args)
                self.after(0, callback, res, None)
            except Exception as e:
                self.after(0, callback, None, e)

        threading.Thread(target=worker, daemon=True).start()


class FileExplorer(tk.Frame):
    def __init__(self, master, ssh_api, start_path=".", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.ssh_api = ssh_api
        self.current_path = start_path

        self.configure(bg="#2d2d2d")

        # Setup the layout: left tree frame and right file list
        self.tree_frame = tk.Frame(self, bg="#2d2d2d")
        self.tree_frame.pack(side="left", fill="y")

        self.content_frame = tk.Frame(self, bg="#2d2d2d")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Directory tree
        self.dir_tree = ttk.Treeview(self.tree_frame, show="tree")
        self.dir_tree.pack(fill="y", expand=True)

        # Style adjustments for dark theme
        style = ttk.Style()
        if sys.platform == "win32":
            # On Windows, you can try 'xpnative' or other themes and then modify their colors
            style.theme_use("default")
        else:
            style.theme_use("default")

        style.configure(
            "Treeview",
            background="#3c3c3c",
            foreground="white",
            fieldbackground="#3c3c3c",
            bordercolor="#3c3c3c",
        )
        style.map("Treeview", background=[("selected", "#555555")])

        # File List
        self.file_list = ttk.Treeview(
            self.content_frame, columns=["Name", "Size", "Modified"], show="headings"
        )
        self.file_list.heading("Name", text="Name")
        self.file_list.heading("Size", text="Size")
        self.file_list.heading("Modified", text="Modified")
        self.file_list.column("Name", anchor="w", width=200)
        self.file_list.column("Size", anchor="e", width=100)
        self.file_list.column("Modified", anchor="w", width=150)
        self.file_list.pack(fill="both", expand=True)

        style.configure("Treeview.Heading", background="#2d2d2d", foreground="white")

        # Bind events
        self.dir_tree.bind("<<TreeviewOpen>>", self.on_dir_expand)
        self.file_list.bind("<Double-1>", self.on_file_open)

        # Populate the root directory in the tree
        root_node = self.dir_tree.insert(
            "", "end", text=start_path, open=True, values=[start_path]
        )
        self.populate_tree(root_node, start_path)

        # Display contents of start_path
        self.display_directory_contents(start_path)

    def populate_tree(self, parent_node, path):
        # We'll load directories asynchronously
        self.run_in_thread(
            self.ssh_api.list_directory_contents,
            (path,),
            lambda result, error: self.on_list_dir_for_tree(
                result, error, parent_node, path
            ),
        )

    def on_list_dir_for_tree(self, items, error, parent_node, path):
        if error:
            # Just ignore errors here or show a message
            return
        # Clear any placeholder
        for child in self.dir_tree.get_children(parent_node):
            if self.dir_tree.item(child, "text") == "...":
                self.dir_tree.delete(child)
        # Insert directories
        for item in items:
            full_path = self.join_path(path, item)
            # We can check directories asynchronously as well
            self.run_in_thread(
                self.ssh_api.is_directory,
                (full_path,),
                lambda is_dir, err: self.on_check_directory(
                    is_dir, err, parent_node, item, full_path
                ),
            )

    def on_check_directory(self, is_dir, error, parent_node, item, full_path):
        if error:
            return
        if is_dir:
            node = self.dir_tree.insert(
                parent_node, "end", text=item, values=[full_path]
            )
            # Add placeholder for lazy loading:
            self.dir_tree.insert(node, "end", text="...")

    def on_dir_expand(self, event):
        node = self.dir_tree.focus()
        node_path = self.dir_tree.item(node, "values")[0]
        # When expanded, re-populate (in case we had placeholders)
        self.populate_tree(node, node_path)
        self.display_directory_contents(node_path)
        self.current_path = node_path

    def on_file_open(self, event):
        selection = self.file_list.focus()
        if not selection:
            return
        item_values = self.file_list.item(selection, "values")
        if not item_values:
            return
        filename = item_values[0]
        full_path = self.join_path(self.current_path, filename)

        # Check if directory or file
        self.run_in_thread(
            self.ssh_api.is_directory,
            (full_path,),
            lambda is_dir, error: self.on_file_open_check(is_dir, error, full_path),
        )

    def on_file_open_check(self, is_dir, error, full_path):
        if error:
            messagebox.showerror("Error", f"Unable to check file type:\n{error}")
            return
        if is_dir:
            self.display_directory_contents(full_path)
            self.current_path = full_path
        else:
            # Open file editor
            FileEditor(self.master, self.ssh_api, full_path)

    def display_directory_contents(self, path):
        # Show loading cursor
        self.master.config(cursor="wait")
        # List directory in thread
        self.run_in_thread(
            self.ssh_api.list_directory_contents,
            (path,),
            lambda items, error: self.on_dir_listed_for_contents(items, error, path),
        )

    def on_dir_listed_for_contents(self, items, error, path):
        self.master.config(cursor="")
        if error:
            messagebox.showerror("Error", f"Unable to list directory:\n{error}")
            return
        # Clear file_list
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        # Now get metadata for each item asynchronously
        # We'll load them one by one to avoid blocking
        # For simplicity, we do them in a loop (could be improved by parallelizing)

        def load_metadata(i=0):
            if i >= len(items):
                return
            filename = items[i]
            full_path = self.join_path(path, filename)
            self.run_in_thread(
                self.ssh_api.get_file_metadata,
                (full_path,),
                lambda meta, err, idx=i, fname=filename: self.on_got_metadata(
                    meta, err, fname, idx, items, path, load_metadata
                ),
            )

        load_metadata(0)

    def on_got_metadata(self, meta, error, filename, index, items, path, callback):
        if error:
            # If we can't get metadata, just skip this file
            pass
        else:
            size = meta["file_size"]
            mod = meta["modification_date"]
            self.file_list.insert("", "end", values=(filename, size, mod))
        # Move to next item
        callback(index + 1)

    def join_path(self, base, name):
        if base.endswith("/"):
            return base + name
        else:
            return base + "/" + name

    def run_in_thread(self, func, args, callback):
        # Generic helper to run blocking SSH calls in a separate thread
        def worker():
            try:
                res = func(*args)
                self.after(0, callback, res, None)
            except Exception as e:
                self.after(0, callback, None, e)

        threading.Thread(target=worker, daemon=True).start()


class DarkApp(tk.Tk):
    def __init__(self, ssh_api, start_path=".", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssh_api = ssh_api
        self.title("SSH File Explorer")

        self.configure(bg="#2d2d2d")

        # Create menu or top bar if desired
        menubar = tk.Menu(self, tearoff=False, bg="#2d2d2d", fg="white")
        filemenu = tk.Menu(menubar, tearoff=False, bg="#2d2d2d", fg="white")
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)

        self.config(menu=menubar)

        self.explorer = FileExplorer(self, self.ssh_api, start_path=start_path)
        self.explorer.pack(fill="both", expand=True)


# Example usage (assuming you have implemented get_file_content and write_file_content in SSHFileSystemApi):

"""
from your_ssh_module import SSHFileSystemApi

# Create the SSH connection


# Make sure you've added:
# 1. A method to read file content, e.g.:
#    def get_file_content(self, path):
#        output = self.execute_command(f"cat {path}")
#        return output
#
# 2. A method to write file content, e.g.:
#    def write_file_content(self, path, content):
#        # You might use echo or a temporary file + mv strategy
#        # For example:
#        temp_path = "/tmp/temp_file.txt"
#        # Escape quotes in content as needed
#        content_escaped = content.replace('"', '\\"')
#        self.execute_command(f'echo "{content_escaped}" > {temp_path} && mv {temp_path} "{path}"')


"""
ssh_api = SSHFileSystemApi(
    host="localhost", port=2222, username="warcock", password="cock"
)

app = DarkApp(ssh_api, start_path=".")
app.mainloop()

# Remember to close SSH connection when done:
ssh_api.close()
