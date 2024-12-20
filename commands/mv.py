from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class MvCommand(BaseCommand):
    name = "mv"
    description = "Moves a file or directory."
    arguments = [
        {"name": "source", "optional": False},
        {"name": "destination", "optional": False},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi") -> None:
        input_path = args[0]
        target_path = args[1]
        if not fs.exists(input_path):
            raise ValueError(f"Error: file or directory '{input_path}' does not exist.")

        if fs.is_directory(input_path) and fs.is_directory(target_path):
            fs.move_directory(input_path, target_path)

        elif not fs.is_directory(input_path) and not fs.is_directory(target_path):
            fs.move_file(input_path, target_path)

        return f"Directory '{input_path}' created successfully."
