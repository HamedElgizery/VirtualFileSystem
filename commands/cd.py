import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.file_system import FileSystem


def cd(args: list, fs: "FileSystem"):
    """
    Simulates the behavior of the 'cd' command, with support for home directory fallback.

    Args:
        args (list): The arguments passed to the command.

    Behavior:
        - If `args` is empty, defaults to the user's home directory.
        - Prints meaningful messages for successful changes or errors.
    """
    # Default to the user's home directory if no path is provided
    if not args:
        path = "~"  # Get the user's home directory
    else:
        path = args[0]

    try:
        # Attempt to change the current working directory
        fs.change_directory(path)
        print(f"Directory successfully changed to: {fs.current_directory}")
    except FileNotFoundError:
        print(f"Error: Directory '{path}' does not exist.")
    except NotADirectoryError:
        print(f"Error: '{path}' is not a directory.")
    except PermissionError:
        print(f"Error: Permission denied to access '{path}'.")
    except OSError as error:
        print(f"Error changing directory to '{path}': {error}")
