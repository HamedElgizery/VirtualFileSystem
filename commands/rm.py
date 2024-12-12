from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List, fs: "FileSystemApi"):
    """
    Simulates the behavior of the 'rm' command to delete a file or a folder.

    Args:
        args (list): The arguments passed to the command.
    """
    if not args:
        print(
            "Error: Missing file or directory name. Usage: rm <file_or_directory_name>"
        )
        return

    target = args[0]

    try:
        if fs.is_directory(target):
            # Remove directory
            fs.delete_directory(target)
            print(f"Directory '{target}' deleted successfully.")
        else:
            # Remove file
            fs.delete_file(target)
            print(f"File '{target}' deleted successfully.")
    except FileNotFoundError:
        print(f"Error: '{target}' not found.")
    except Exception as e:
        print(f"Error: Unable to delete '{target}'. {e}")
