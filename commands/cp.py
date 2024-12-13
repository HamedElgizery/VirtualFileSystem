from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class CpCommand(BaseCommand):

    name = "cp"
    description = "Copies a file."
    arguments = [
        {"name": "source", "optional": False},
        {"name": "destination", "optional": False},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        source = args[0]
        destination = args[1]

        if not fs.exists(source):
            raise ValueError(f"Error: Source file '{source}' does not exist.")

        if fs.is_directory(source):
            raise ValueError(
                f"Error: Source '{source}' is a directory. Only file copying is supported."
            )

        if not fs.is_directory(destination):
            raise ValueError(f"Destination '{destination}' is not a directory.")

        try:
            fs.copy_file(source, destination)
            return f"File '{source}' copied to '{destination}' successfully."
        except OSError as error:
            raise Exception(
                f"Error copying file '{source}' to '{destination}': {error}"
            )
