from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class RmCommand(BaseCommand):
    name = "rm"
    description = "Removes a file or directory."
    arguments = [{"name": "path", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        path = args[0]
        if not fs.is_directory(path):
            fs.delete_file(path)
        elif fs.is_directory(path):
            fs.delete_directory(path)
        else:
            raise FileNotFoundError(f"{path} not found")
        return ""
