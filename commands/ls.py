"""
Lists the contents of the current directory.

:param fs: The file system.
:param args: The command line arguments.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(
    args: list,
    fs: "FileSystemApi",
):
    if len(args) > 1:
        print("Error: too many arguments for ls command")
        return

    current_dir = args[0] if args else ""
    if args and args[0] == "-l":
        files = fs.list_directory_contents(current_dir)
        for file in files:
            file_index = fs.get_file_metadata(file)
            if file_index:
                print(
                    f"{file_index.file_name}\t{file_index.file_size}\t{file_index.creation_date}"
                )
            else:
                print(f"{file}")
    else:
        files = fs.list_directory_contents(current_dir)
        for file in files:
            print(file)
