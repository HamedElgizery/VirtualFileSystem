import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from file_system_api import FileSystemApi
import tkinter.filedialog as fd


class ConnectionWindow:
    """Handles the connection interface for the user."""

    def __init__(self, root):
        self.root = root
        self.root.title("GUI Client")

        self._initialize_widgets()

    def _initialize_widgets(self):
        tk.Label(self.root, text="Username:").grid(row=0, column=0, padx=5, pady=5)

        self.username_entry = tk.Entry(self.root)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Connect", command=self.connect).grid(
            row=1, column=0, columnspan=2, pady=10
        )

    def connect(self):
        username = self.username_entry.get()
        try:
            client = self._get_client(username)
            self.root.destroy()
            MainGUI(client)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")

    def _get_client(self, username):
        if FileSystemApi.file_system_exists(username):
            return FileSystemApi(username)
        return FileSystemApi.create_new_file_system(username)


class MainGUI:
    """Manages the main GUI for file exploration."""

    def __init__(self, client: "FileSystemApi"):
        self.client = client
        self.history = []
        self.history_index = -1
        self.copy_buffer = None
        self.copy_buffer_mode = None

        self.root = TkinterDnD.Tk()
        self.root.title("GUI File Explorer")

        self._initialize_navigation_bar()
        self._initialize_treeview()
        self._initialize_context_menus()
        self._initialize_right_click_menu()

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind("<<Drop>>", self.on_file_drop)

        self.load_directory(self.client.current_directory)

    def _initialize_navigation_bar(self):
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)

        self.back_button = tk.Button(
            nav_frame, text="Back", command=self.go_back, state=tk.DISABLED
        )
        self.back_button.pack(side=tk.LEFT, padx=5)

        self.forward_button = tk.Button(
            nav_frame, text="Forward", command=self.go_forward, state=tk.DISABLED
        )
        self.forward_button.pack(side=tk.LEFT, padx=5)

        self.address_bar = tk.Entry(nav_frame)
        self.address_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        tk.Button(nav_frame, text="Go", command=self.navigate_to_address).pack(
            side=tk.LEFT, padx=5
        )

    def _initialize_treeview(self):
        self.tree = ttk.Treeview(
            self.root,
            columns=("Name", "Size", "Type", "Last Modified"),
            show="headings",
        )
        self.tree.heading("Name", text="Name")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Last Modified", text="Last Modified")
        self.tree.bind("<Double-1>", self.on_tree_click)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _initialize_context_menus(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy)
        self.context_menu.add_command(label="Move", command=self.move)
        self.context_menu.add_command(label="Delete", command=self.delete)
        self.context_menu.add_command(label="Save to PC", command=self.save_to_pc)

        self.tree.bind("<Button-3>", self._show_context_menu, add="+")

    def _initialize_right_click_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Create Folder", command=self.create_folder)
        self.menu.add_command(label="Create File", command=self.create_file)

        self.tree.bind("<Button-3>", self._show_menu, add="+")

    def on_file_drop(self, event):
        file_path = event.data.strip()
        try:
            self._handle_file_drop(file_path)
        except Exception as e:
            print(f"Error handling file drop: {e}")

    def _handle_file_drop(self, file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_data = f.read()

        self.client.create_file(file_name, file_data)
        self.load_directory(self.client.current_directory)
        print(f"File dropped: {file_path}")

    def paste_buffer(self):
        if not self.copy_buffer or not self.copy_buffer_mode:
            return

        self._handle_paste()
        self.copy_buffer = None
        self.copy_buffer_mode = None
        self.menu.delete("Paste")
        self.load_directory(self.client.current_directory)

    def _handle_paste(self):
        if self.copy_buffer_mode == "copy":
            self._copy_item()
        elif self.copy_buffer_mode == "move":
            self._move_item()

    def _copy_item(self):
        if self.client.is_directory(self.copy_buffer):
            self.client.copy_directory(self.copy_buffer, self.client.current_directory)
        else:
            self.client.copy_file(self.copy_buffer, self.client.current_directory)

    def _move_item(self):
        if self.client.is_directory(self.copy_buffer):
            self.client.move_directory(self.copy_buffer, self.client.current_directory)
        else:
            self.client.move_file(self.copy_buffer, self.client.current_directory)

    def move(self):
        self._set_copy_buffer("move")

    def copy(self):
        self._set_copy_buffer("copy")

    def save_to_pc(self):
        selected_item = self.tree.selection()[0]

        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a file to save.")
            return

        item_values = self.tree.item(selected_item, "values")
        file_name = item_values[0]

        if not file_name:
            messagebox.showwarning("No Selection", "Please select a file to save.")
            return

        if self.client.is_directory(file_name):
            messagebox.showwarning("Invalid File", "Selected item is not a file.")
            return

        initialdir = os.path.expanduser("~")
        file_path = fd.asksaveasfilename(
            initialdir=initialdir,
            initialfile=file_name,
            title="Save As",
            filetypes=(("All Files", "*.*"),),
        )

        if file_path:
            try:
                file_data = self.client.read_file(file_name)
                with open(file_path, "wb") as f:
                    f.write(file_data)
                messagebox.showinfo("Success", f"File saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def _set_copy_buffer(self, mode):
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, "values")
        self.copy_buffer = self.client.resolve_path(item_values[0])
        self.copy_buffer_mode = mode
        self.menu.add_command(label="Paste", command=self.paste_buffer)

    def delete(self):
        self._delete_item()
        self.load_directory(self.client.current_directory)

    def _delete_item(self):
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, "values")
        if not self.client.is_directory(item_values[0]):
            self.client.delete_file(item_values[0])
        else:
            self.client.delete_directory(item_values[0])

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._handle_tree_click(item)

    def _handle_tree_click(self, item):
        item_values = self.tree.item(item, "values")
        if item_values and item_values[2] != "Directory":
            self._open_file(item_values[0])
        elif item_values:

            self._navigate_to_directory(item_values[0])

    def _navigate_to_directory(self, directory):

        self.client.change_directory(directory)
        self.load_directory(self.client.current_directory)

    def _open_file(self, file_name):
        file_path = os.path.join(self.client.current_directory, file_name)
        self._create_file_window(file_path)

    def _create_file_window(self, file_path):
        file_window = tk.Toplevel(self.root)
        file_window.title(file_path)
        text = tk.Text(file_window, width=40, height=10)
        text.pack(fill=tk.BOTH, expand=True)

        text.insert(tk.END, self.client.read_file(file_path).decode())
        file_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._close_file_window(file_window, text, file_path),
        )

    def _close_file_window(self, file_window, text, file_path):
        if (
            text.get("1.0", tk.END).strip()
            != self.client.read_file(file_path).decode().strip()
        ):
            if messagebox.askokcancel(
                "Save changes?", "Do you want to save changes to the file?"
            ):
                self.save_file(file_window, text, file_path)
        file_window.destroy()

    def save_file(self, file_window, text_box, file_path):
        self.client.edit_file(file_path, text_box.get("1.0", tk.END).encode())
        file_window.destroy()

    def create_folder(self):
        self._create_input_window(
            "Create Folder", "Folder Name:", self.client.create_directory
        )

    def create_file(self):
        self._create_input_window("Create File", "File Name:", self._create_new_file)

    def _create_new_file(self, file_name):
        self.client.create_file(file_name, b"")

    def _create_input_window(self, title, label_text, callback):
        window = tk.Toplevel(self.root)
        window.title(title)

        tk.Label(window, text=label_text).grid(row=0, column=0, padx=5, pady=5)

        entry = tk.Entry(window)
        entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            window,
            text="Create",
            command=lambda: self._execute_callback(callback, entry, window),
        ).grid(row=1, column=0, columnspan=2, pady=5)

    def _execute_callback(self, callback, entry, window):
        value = entry.get()
        if value:
            callback(value)
            entry.delete(0, tk.END)
            window.destroy()
            self.load_directory(self.client.current_directory)

    def load_directory(self, path):
        try:
            self._populate_tree(path)
            self.address_bar.delete(0, tk.END)
            self.address_bar.insert(0, path)
            self._update_history(path)
            self.update_nav_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load directory: {str(e)}")

    def _populate_tree(self, path):
        self.tree.delete(*self.tree.get_children())
        items = self.client.list_directory_contents(path)
        for item in items:
            details = self.client.get_file_metadata(os.path.join(path, item))
            self.tree.insert(
                "",
                "end",
                values=(
                    details.file_name,
                    f"{details.file_size} bytes",
                    "Directory" if details.is_directory else "File",
                    details.modification_date,
                ),
            )

    def _update_history(self, path):
        if self.history_index == -1 or self.history[self.history_index] != path:
            self.history = self.history[: self.history_index + 1]
            self.history.append(path)
            self.history_index += 1

    def update_nav_buttons(self):
        self.back_button.config(
            state=tk.NORMAL if self.history_index > 0 else tk.DISABLED
        )
        self.forward_button.config(
            state=(
                tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED
            )
        )

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.client.change_directory(self.history[self.history_index])
            self.load_directory(self.client.current_directory)

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.client.change_directory(self.history[self.history_index])
            self.load_directory(self.client.current_directory)

    def navigate_to_address(self):
        path = self.address_bar.get()
        self.load_directory(path)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _show_menu(self, event):
        if not self.tree.identify_row(event.y):
            self.menu.post(event.x_root, event.y_root)


if __name__ == "__main__":
    root = tk.Tk()
    ConnectionWindow(root)
    root.mainloop()
