import os
from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class IsDirCommand(BaseCommand):
    name = "is_dir"
    description = "Checks if the given path is a directory."
    arguments = [{"name": "path", "optional": False}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        path = args[0]

        output = "true" if fs.is_directory(path) else "false"

        return output
