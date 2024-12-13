from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class RenameCommand(BaseCommand):
    name = "rename"
    description = "Renames a file or directory."
    arguments = [
        {"name": "old_name", "optional": False},
        {"name": "new_name", "optional": False},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        old_name, new_name = args[0], args[1]
        if not fs.exists(old_name):
            raise Exception(f"Error: File '{old_name}' not found.")

        if fs.exists(new_name):
            raise Exception(f"Error: File '{new_name}' already exists.")

        fs.rename_file(old_name, new_name)
        return f"File '{old_name}' renamed to '{new_name}' successfully."
