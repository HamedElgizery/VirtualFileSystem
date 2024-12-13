from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class CatCommand(BaseCommand):
    name = "cat"
    description = "Prints the contents of a file to the console."
    arguments = [{"name": "file_path", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        file_path = args[0]

        file_contents = fs.read_file(file_path)

        return file_contents.decode()
