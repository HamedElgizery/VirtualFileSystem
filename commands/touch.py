from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class TouchCommand(BaseCommand):
    name = "touch"
    description = "Creates a new file or updates a file's last modified time."
    arguments = [{"name": "file_path", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        file_path = args[0]

        if fs.exists(file_path):
            if fs.is_directory(file_path):
                raise ValueError(f"The path '{file_path}' is a directory.")

            fs.file_system.update_file_access_time(file_path)
        else:
            fs.create_empty_file(file_path)
        return ""
