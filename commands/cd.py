import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file_system_api import FileSystemApi
"""
Simulates the behavior of the 'cd' command, with support for home directory fallback.

Args:
    args (list): The arguments passed to the command.

Behavior:
    - If `args` is empty, defaults to the user's home directory.
    - Prints meaningful messages for successful changes or errors.
"""


def execute(args: list, fs: "FileSystemApi"):

    # Default to the user's home directory if no path is provided
    if not args:
        path = fs.current_directory
    else:
        path = args[0]

    resolved_path = fs.resolve_path(path)
    if not fs.is_valid_path(resolved_path):
        print(f"Error: Directory '{path}' does not exist.")
        return

    try:
        fs.change_directory(resolved_path)
        print(f"Directory successfully changed to: {fs.current_directory}")
    except NotADirectoryError:
        print(f"Error: '{path}' is not a directory.")
    except PermissionError:
        print(f"Error: Permission denied to access '{path}'.")
    except OSError as error:
        print(f"Error changing directory to '{path}': {error}")
