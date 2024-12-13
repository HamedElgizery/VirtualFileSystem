from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class MkdirCommand(BaseCommand):
    """
    Simulates the behavior of the 'mkdir' command to create a directory.

    Usage:
      mkdir <directory_name>
    """

    name = "mkdir"
    description = "Creates a directory."
    arguments = [{"name": "directory_name", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        directory_name = args[0]
        fs.create_directory(directory_name)
        return f"Directory '{directory_name}' created successfully."
