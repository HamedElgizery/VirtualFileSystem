from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class CdCommand(BaseCommand):
    name = "cd"
    description = "Changes the current working directory to the one specified."
    arguments = [{"name": "path", "optional": True}]

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        if not args:
            path = fs.current_directory
        else:
            path = args[0]

        resolved_path = fs.resolve_path(path)
        if not fs.is_valid_path(resolved_path):
            return f"Error: Directory '{path}' does not exist."

        try:
            fs.change_directory(resolved_path)
            return f"Directory successfully changed to: {fs.current_directory}"
        except NotADirectoryError:
            return f"Error: '{path}' is not a directory."
        except PermissionError:
            return f"Error: Permission denied to access '{path}'."
        except OSError as error:
            return f"Error changing directory to '{path}': {error}"
