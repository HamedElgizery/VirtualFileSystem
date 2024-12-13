from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class LsCommand(BaseCommand):
    name = "ls"
    description = "Lists the contents of the current directory."
    arguments = [
        {"name": "path", "optional": True},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        output = ""

        path = args[0] if args else "."
        if fs.is_directory(path):
            contents = fs.list_directory_contents(path)
            for item in contents:
                output += f"{item}\n"
        else:
            output += f"{path} is not a directory."

        if output and output[-1] == "\n":
            output = output[:-1]

        return output
