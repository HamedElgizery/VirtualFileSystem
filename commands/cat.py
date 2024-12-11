from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.file_system import FileSystem


"""
Prints the contents of a file to the console.

Usage:
  cat <file>
"""


def execute(args: List, fs: "FileSystem"):
    """
    Prints the contents of a file to the console.

    :param args: The command line arguments.
    :param fs: The file system.
    """
    if len(args) != 1:
        print("Error: invalid number of arguments")
        return

    file_path = args[0]

    file_contents = fs.read_file(file_path)

    print(file_contents.decode())
