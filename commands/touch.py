"""
Simulates the behavior of the 'touch' command to create a new file or update a file's last modified time.

Usage:
  touch <file_name>

"""

import os
import time
from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List, fs: "FileSystemApi"):
    # Remove leading/trailing spaces from the argument
    arg = args[0].strip()

    # Check if the argument is empty (no file name provided)
    if not arg:
        print("Error: Missing file name. Usage: touch <file_name>")
        return

    try:
        # Check if the file already exists
        if fs.exists(arg):
            fs.file_system.update_file_access_time(arg)
        else:
            # If file doesn't exist, create it in append mode (so it won't overwrite existing content)
            fs.create_empty_file(arg)

    except OSError as e:
        # Handle any OS-related errors and print a message
        print(f"Error: Unable to create or modify file '{arg}'. {e}")
