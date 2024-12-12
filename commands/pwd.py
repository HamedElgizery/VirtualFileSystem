"""Simulates the behavior of the 'pwd' command to print the current working directory."""

import os
from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List[str], fs: "FileSystemApi"):

    # Check if any argument is passed (though pwd typically doesn't take any argument)
    if args:
        print("Error: 'pwd' command does not take any arguments.")
        return

    print(f"Current working directory: {fs.current_directory}")
