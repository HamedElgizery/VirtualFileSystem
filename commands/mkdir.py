import os
import shutil
from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List, fs: "FileSystemApi" = None):
    """Simulates the behavior of the 'mkdir' command to create a directory or edit an existing one.

    Args:
        arg (str): The name or path of the directory to create.
        edit_dir (str, optional): New name or path to rename or move the directory.
    """
    arg = args[0]
    edit_dir = args[1] if len(args) > 1 else None
    # Check if the directory name is provided
    if not arg:
        print("Error: Missing directory name. Usage: mkdir <directory_name>")
        return

    try:
        if edit_dir:
            # Edit (rename or move) the directory
            if not fs.exists(arg):
                print(f"Error: Source directory '{arg}' does not exist.")
                return
            fs.move_directory(arg, edit_dir)
            print(f"Directory '{arg}' renamed/moved to '{edit_dir}' successfully.")
        else:
            # Create the directory
            fs.create_directory(arg)
            print(f"Directory '{arg}' created successfully.")
    except Exception as e:
        # Handle exceptions
        print(f"Error: Unable to process directory '{arg}'. {e}")
