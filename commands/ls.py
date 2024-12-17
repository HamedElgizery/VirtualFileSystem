import os
from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class LsCommand(BaseCommand):
    name = "ls"
    description = "Lists the contents of the current directory."
    arguments = [
        {"name": "path", "optional": True},
        {"name": "-l", "optional": True},
    ]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        output = ""
        path = "."

        if len(args) > 0 and not args[0].startswith("-"):
            path = args[0] if args else "."

        use_long_format = "-l" in args

        if fs.is_directory(path):
            contents = fs.list_directory_contents(path)
            if use_long_format:
                for item in contents:
                    metadata = fs.get_file_metadata(os.path.join(path, item))
                    output += (
                        f"{item} {metadata.file_size} {metadata.modification_date}\n"
                    )
            else:
                for item in contents:
                    output += f"{item}\n"
        else:
            output += f"{path} is not a directory."

        if output and output[-1] == "\n":
            output = output[:-1]

        return output
