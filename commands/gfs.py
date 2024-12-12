from typing import TYPE_CHECKING, List

from file_system_api import FileSystemApi


if TYPE_CHECKING:
    from file_system_api import FileSystemApi

"""Retrieves the size of a file in bytes.

Args:
    args (List[str]): The arguments passed to the command.
    fs (FileSystemApi): The file system to use.

Returns:
    str: The size of the file in bytes.
"""


def execute(args: List[str], fs: FileSystemApi):

    if not args:
        print("Error: Missing file name. Usage: get_file_size <file_name>")
        return

    file_path = args[0]
    try:
        file_size = fs.get_file_size(file_path)
        print(f"{file_path}: {file_size}")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IsADirectoryError:
        print(f"Error: '{file_path}' is a directory, not a file.")
