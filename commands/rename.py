from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: List[str], fs: "FileSystemApi") -> None:
    """Renames a file.

    Args:
        args (List[str]): The list of arguments to be passed to the command.
        fs (FileSystemApi): The file system to use.
    """
    if len(args) != 2:
        print("Error: wrong number of arguments. Usage: rename <old_name> <new_name>")
        return

    old_name = args[0]
    new_name = args[1]

    try:
        if not fs.exists(old_name):
            print(f"Error: File '{old_name}' not found.")
            return

        if fs.exists(new_name):
            print(f"Error: File '{new_name}' already exists.")
            return

        fs.rename_file(old_name, new_name)
        print(f"File '{old_name}' renamed to '{new_name}' successfully.")

    except OSError as error:
        print(f"Error renaming file: {error}")
