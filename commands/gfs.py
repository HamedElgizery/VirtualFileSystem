from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class GfsCommand(BaseCommand):
    name = "gfs"
    description = "Gets the size of a file in bytes."
    arguments = [{"name": "file_path", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        file_path = args[0]

        file_size = fs.get_file_size(file_path)

        return str(file_size)
