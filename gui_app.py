"""
This is the gui of the file system, it connects using username.
"""

import io
import os
import tkinter as tk
from tkinter import Canvas, ttk, messagebox
import tkinter.filedialog as fd
from typing import Callable, List, Optional
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
from file_system_api import FileSystemApi


def set_window_to_center(root: tk.Tk) -> None:
    """Sets a tkinter window to the center of the screen

    Args:
        root (tk.Tk): The window to set.
    """
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")


def is_command_in_menu(menu, command_name):
    try:
        for i in range(menu.index("end") + 1):  # Iterate over all menu items
            if menu.entrycget(i, "label") == command_name:
                return True
    except:
        pass  # Safeguard against any errors (e.g., non-existent indexes)
    return False


class ConnectionWindow:
    """Handles the connection interface for the user."""

    def __init__(self) -> None:
        root = tk.Tk()
        self.root = root
        self.root.title("GUI Client")
        self._initialize_widgets()
        set_window_to_center(self.root)
        root.mainloop()

    def _initialize_widgets(self) -> None:
        """
        Putting the widgets in the window to get the username.
        """
        tk.Label(self.root, text="Username:").grid(row=0, column=0, padx=5, pady=5)

        self.username_entry = tk.Entry(self.root)
        self.username_entry.bind("<Return>", lambda event: self.connect())
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Connect", command=self.connect).grid(
            row=1, column=0, columnspan=2, pady=10
        )

    def connect(self) -> None:
        """
        Connecting to file system and creating new window
        """
        username = self.username_entry.get()
        if username.strip() == "":
            messagebox.showerror("Error", "Please enter a username.")
            return
        try:
            client = self._get_client(username)
            self.root.destroy()
            MainGUI(client)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")

    def _get_client(self, username: str) -> "FileSystemApi":
        if FileSystemApi.file_system_exists(username):
            return FileSystemApi(username)
        return FileSystemApi.create_new_file_system(username)


class MainGUI:
    """Manages the main GUI for file exploration."""

    def __init__(self, client: "FileSystemApi") -> None:
        self.client = client
        self.history: List[str] = []
        self.history_index = -1
        self.copy_buffer: Optional[str] = None
        self.copy_buffer_mode: Optional[str] = None

        self.root = TkinterDnD.Tk()
        self.root.title("GUI File Explorer")

        self._initialize_navigation_bar()
        self._initialize_treeview()
        self._initialize_context_menus()
        self._initialize_right_click_menu()
        set_window_to_center(self.root)

        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind("<<Drop>>", self.on_file_drop)

        self.load_directory(self.client.current_directory)

    def _initialize_navigation_bar(self) -> None:
        """Initializes the navigation bar containing back, forward, address bar, and go buttons."""
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

    def _initialize_treeview(self) -> None:
        """
        Initializes the treeview widget with columns for name, size, type, and
        last modified date. The treeview is bound to the double left click event
        to trigger the on_tree_click method. The treeview is then packed into the
        main window with padding and expanding to fill available space.
        """
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
        self.tree.bind("<Control-c>", lambda _: self.copy())
        self.tree.bind("<Control-x>", lambda _: self.move())
        self.tree.bind("<Control-v>", lambda _: self.paste_buffer())

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _initialize_context_menus(self) -> None:
        """
        Initializes the context menu with options to copy, move, delete, and
        save to PC. The context menu is bound to the right click event on the
        treeview widget.
        """
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy)
        self.context_menu.add_command(label="Move", command=self.move)
        self.context_menu.add_command(label="Delete", command=self.delete)
        self.context_menu.add_command(label="Save to PC", command=self.save_to_pc)

        self.tree.bind("<Button-3>", self._show_context_menu, add="+")

    def _initialize_right_click_menu(self) -> None:
        """
        Initializes the right click menu with options to create a folder and
        create a file. The menu is bound to the right click event on the
        treeview widget.
        """
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Create Folder", command=self.create_folder)
        self.menu.add_command(label="Create File", command=self.create_file)

        self.tree.bind("<Button-3>", self._show_menu, add="+")

    def on_file_drop(self, event: tk.Event) -> None:
        """
        Handles the event when a file is dropped onto the treeview widget.

        :param event: The event object containing the dropped file path.
        """
        file_path = event.data.strip()
        try:
            self._handle_file_drop(file_path)
        except Exception as e:
            print(f"Error handling file drop: {e}")

    def _handle_file_drop(self, file_path: str) -> None:
        """
        Handles the event when a file is dropped onto the treeview widget.

        :param file_path: The path of the dropped file.
        """
        clean_path = file_path.strip("{}")
        file_name = os.path.basename(clean_path)
        normalized_path = os.path.normpath(clean_path)
        with open(normalized_path, "rb") as f:
            file_data = f.read()

        self.client.create_file(file_name, file_data)
        self.load_directory(self.client.current_directory)
        print(f"File dropped: {file_path}")

    def paste_buffer(self) -> None:
        """
        Pastes the contents of the copy buffer into the current directory.
        """
        if not self.copy_buffer or not self.copy_buffer_mode:
            return

        self._handle_paste()
        self.copy_buffer = None
        self.copy_buffer_mode = None
        self.menu.delete("Paste")
        self.load_directory(self.client.current_directory)

    def _handle_paste(self) -> None:
        """
        Handles the paste operation based on the current copy buffer mode.
        """
        if self.copy_buffer_mode == "copy":
            self._copy_item()
        elif self.copy_buffer_mode == "move":
            self._move_item()

    def _copy_item(self) -> None:
        if self.client.is_directory(self.copy_buffer):
            self.client.copy_directory(self.copy_buffer, self.client.current_directory)
        else:
            self.client.copy_file(self.copy_buffer, self.client.current_directory)

    def _move_item(self) -> None:
        if self.client.is_directory(self.copy_buffer):
            self.client.move_directory(self.copy_buffer, self.client.current_directory)
        else:
            self.client.move_file(self.copy_buffer, self.client.current_directory)

    def move(self) -> None:
        self._set_copy_buffer("move")

    def copy(self) -> None:
        self._set_copy_buffer("copy")

    def save_to_pc(self) -> None:
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

    def _set_copy_buffer(self, mode: str) -> None:
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, "values")
        self.copy_buffer = self.client.resolve_path(item_values[0])
        self.copy_buffer_mode = mode
        if not is_command_in_menu(self.menu, "Paste"):
            self.menu.add_command(label="Paste", command=self.paste_buffer)

    def delete(self) -> None:
        self._delete_item()
        self.load_directory(self.client.current_directory)

    def _delete_item(self) -> None:
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, "values")
        if not self.client.is_directory(item_values[0]):
            self.client.delete_file(item_values[0])
        else:
            self.client.delete_directory(item_values[0])

    def on_tree_click(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self._handle_tree_click(item)

    def _handle_tree_click(self, item: str) -> None:
        item_values = self.tree.item(item, "values")
        if item_values and item_values[2] != "Directory":
            self._open_file(item_values[0])
        elif item_values:

            self._navigate_to_directory(item_values[0])

    def _navigate_to_directory(self, directory: str) -> None:

        self.client.change_directory(directory)
        self.load_directory(self.client.current_directory)

    def _open_file(self, file_name: str) -> None:
        file_path = self.client.normalize_path(
            os.path.join(self.client.current_directory, file_name)
        )
        _, file_extension = os.path.splitext(file_name)

        if file_extension in [".jpg", ".png", ".jpeg"]:
            self._create_image_window(file_path)
        else:
            self._create_file_window(file_path)

    def _create_file_window(self, file_path: str) -> None:
        file_window = tk.Toplevel(self.root)

        file_window.title(file_path)
        text = tk.Text(file_window, width=40, height=10)
        text.pack(fill=tk.BOTH, expand=True)

        text.insert(tk.END, self.client.read_file(file_path).decode())
        set_window_to_center(file_window)

        file_window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._close_file_window(file_window, text, file_path),
        )

    def _close_file_window(
        self, file_window: tk.Tk, text: tk.Text, file_path: str
    ) -> None:
        """
        Closes the file window, optionally saving changes.

        :param file_window: The Tkinter window displaying the file contents.
        :param text: The Tkinter Text widget containing the file content.
        :param file_path: The path of the file being edited.
        """
        if (
            text.get("1.0", tk.END).strip()
            != self.client.read_file(file_path).decode().strip()
        ):
            if messagebox.askokcancel(
                "Save changes?", "Do you want to save changes to the file?"
            ):
                self.save_file(file_window, text, file_path)
        file_window.destroy()

    def save_file(self, file_window: tk.Tk, text_box: tk.Text, file_path: str) -> None:
        """
        Saves the changes to a file and closes the file window.

        :param file_window: The window containing the file text box.
        :param text_box: The text box with the file content.
        :param file_path: The path of the file to be saved.
        :return: None
        """
        self.client.edit_file(file_path, text_box.get("1.0", tk.END).encode())
        file_window.destroy()

    def create_folder(self) -> None:
        """
        Opens a window to create a new folder.

        :return: None
        """
        self._create_input_window(
            "Create Folder", "Folder Name:", self.client.create_directory
        )

    def create_file(self) -> None:
        """
        Opens a window to create a new file.

        :return: None
        """
        self._create_input_window("Create File", "File Name:", self._create_new_file)

    def _create_new_file(self, file_name: str) -> None:
        """
        Creates a new file with the given name.

        :param file_name: The name of the file to be created.
        """
        self.client.create_file(file_name, b"")

    def _create_input_window(
        self, title: str, label_text: str, callback: Callable
    ) -> None:
        """
        Creates a window with a text label and input field that can be used to get a
        string from the user.

        :param title: The title of the window.
        :param label_text: The text to be displayed next to the input field.
        :param callback: The function to be called when the user presses the "Create" button.
                         The function should take one argument, the string from the input field.
        """
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

    def _execute_callback(
        self, callback: Callable, entry: tk.Entry, window: tk.Tk
    ) -> None:
        """
        Executes the given callback with the value from the given entry.

        :param callback: The function to be called when the user presses the "Create" button.
                         The function should take one argument, the string from the input field.
        :param entry: The Entry widget containing the input string.
        :param window: The Toplevel window to be destroyed after the callback is executed.
        """

        value = entry.get()
        if value:
            callback(value)
            entry.delete(0, tk.END)
            window.destroy()
            self.load_directory(self.client.current_directory)

    def load_directory(self, path: str) -> None:
        """
        Loads and displays the contents of the specified directory in the GUI.

        :param path: The path of the directory to load.
        :return: None
        """
        try:
            self._populate_tree(path)
            self.address_bar.delete(0, tk.END)
            self.address_bar.insert(0, path)
            self._update_history(path)
            self.update_nav_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load directory: {str(e)}")

    def _populate_tree(self, path: str) -> None:
        """
        Populates the tree view with the contents of the specified directory.

        :param path: The path of the directory to populate in the tree view.
        """
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

    def _update_history(self, path) -> None:
        """
        Updates the history of directories visited.

        :param path: The path of the directory to add to the history.
        :return: None
        """
        if self.history_index == -1 or self.history[self.history_index] != path:
            self.history = self.history[: self.history_index + 1]
            self.history.append(path)
            self.history_index += 1

    def update_nav_buttons(self) -> None:
        """
        Updates the state of the navigation buttons based on the current history index.

        :return: None
        """
        self.back_button.config(
            state=tk.NORMAL if self.history_index > 0 else tk.DISABLED
        )
        self.forward_button.config(
            state=(
                tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED
            )
        )

    def go_back(self) -> None:
        """
        Navigates to the previous directory in the history, if available.

        :return: None
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.client.change_directory(self.history[self.history_index])
            self.load_directory(self.client.current_directory)

    def go_forward(self) -> None:
        """
        Navigates to the next directory in the history, if available.

        :return: None
        """

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.client.change_directory(self.history[self.history_index])
            self.load_directory(self.client.current_directory)

    def navigate_to_address(self) -> None:
        """
        Navigates to the path specified in the address bar.

        :return: None
        """
        path = self.address_bar.get()
        self.load_directory(path)

    def _show_context_menu(self, event: tk.Event) -> None:
        """
        Shows the context menu at the position of the given event, if the event is over an item.

        :param event: The event that triggered the context menu.
        :return: None
        """
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _show_menu(self, event: tk.Event) -> None:
        """
        Shows the menu at the position of the given event.

        :param event: The event that triggered the menu.
        :return: None
        """
        if not self.tree.identify_row(event.y):
            self.menu.post(event.x_root, event.y_root)

    def _create_image_window(self, file_path: str) -> None:
        """
        Create a Tkinter window and display an image from bytes.

        :param image_bytes: The image data in bytes format.
        """
        image_bytes = self.client.read_file(file_path)

        window = tk.Toplevel(self.root)
        window.title("Image Viewer")

        image = Image.open(io.BytesIO(image_bytes))

        tk_image = ImageTk.PhotoImage(image)
        panel = tk.Label(window, image=tk_image)
        panel.image = tk_image
        panel.pack()
        window.mainloop()


if __name__ == "__main__":
    ConnectionWindow()
