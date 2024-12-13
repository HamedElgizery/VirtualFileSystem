from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class PwdCommand(BaseCommand):
    name = "pwd"
    description = "Prints the current working directory."
    arguments = []

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        return fs.current_directory
