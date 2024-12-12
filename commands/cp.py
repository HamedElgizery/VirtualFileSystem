import os
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from file_system_api import FileSystemApi

"""Simulates the behavior of the 'cp' command to copy a file.

Args:
    args (List[str]): The command line arguments.
    fs (FileSystemApi): The file system.
"""


def execute(args: List[str], fs: "FileSystemApi"):

    if len(args) != 2:
        print("Error: wrong number of arguments. Usage: cp <source> <destination>")
        return

    source = args[0]
    destination = args[1]

    # Check if the source exists
    if not fs.exists(source):
        print(f"Error: Source file '{source}' does not exist.")
        return

    # If the source is a directory, raise an error (currently only handles files)
    if fs.is_directory(source):
        print(
            f"Error: Source '{source}' is a directory. Only file copying is supported."
        )
        return

    # Check if the destination is a directory (for copying the file into a directory)
    if not fs.is_directory(destination):
        raise ValueError(f"Destination '{destination}' is not a directory.")

    try:
        # Copy the file
        fs.copy_file(source, destination)
        print(f"File '{source}' copied to '{destination}' successfully.")
    except OSError as error:
        print(f"Error copying file '{source}' to '{destination}': {error}")
