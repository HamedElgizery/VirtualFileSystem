from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class EchoCommand(BaseCommand):
    name = "echo"
    description = "Echoes a message or writes it to a file."
    arguments = [
        {"name": "message", "optional": False},
        {"name": "file_path", "optional": True},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi"):
        message = args[0]
        return message
