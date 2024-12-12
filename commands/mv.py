"""
Simulates the behavior of the 'mv' command to move or rename files/directories.

Args:
    args (List[str]): The list of arguments to be passed to the command.
    fs (FileSystemApi): The file system to use.
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List[str], fs: "FileSystemApi") -> None:

    if len(args) != 2:
        print("Error: wrong number of arguments. Usage: mv <source> <destination>")
        return

    source, destination = args[0].strip(), args[1].strip()

    try:
        if not fs.exists(source):
            print(f"Error: Source '{source}' does not exist.")
            return

        if fs.is_directory(destination):
            destination = fs.join_path(destination, fs.get_basename(source))

        fs.move_file(source, destination)
        print(f"'{source}' has been moved/renamed to '{destination}' successfully.")
    except FileNotFoundError:
        print(f"Error: Destination '{destination}' does not exist.")
    except PermissionError:
        print(f"Error: Permission denied while moving to '{destination}'.")
    except OSError as error:
        print(f"Error: Unable to move/rename '{source}' to '{destination}'. {error}")
