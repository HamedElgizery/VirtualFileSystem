from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class BaseCommand(ABC):
    name: str
    description: str
    arguments: List[Dict[str, Any]]

    def __init__(self):

        if not hasattr(self, "name") or not self.name:
            raise ValueError("Command must have a 'name' attribute.")
        if not hasattr(self, "description") or not self.description:
            self.description = "No description available."
        if not hasattr(self, "arguments") or not isinstance(self.arguments, list):
            self.arguments = []

    @abstractmethod
    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        pass

    def run(self, args: List[str], fs: "FileSystemApi"):
        target_file, append_mode = self._parse_redirection(args)

        # Validate and execute the command
        self.validate_args(args)
        output = self.execute(args, fs)

        # Handle output
        if target_file:
            self._write_output_to_file(output, target_file, append_mode, fs)
        else:
            if output.strip():
                print(output)

    def _parse_redirection(self, args: List[str]) -> Tuple[Optional[str], bool]:
        if ">>" in args:
            idx = args.index(">>")
            target_file = args[idx + 1]
            del args[idx:]
            return target_file, True
        elif ">" in args:
            idx = args.index(">")
            target_file = args[idx + 1]
            del args[idx:]
            return target_file, False
        return None, False

    def _write_output_to_file(
        self, output: str, file_path: str, append_mode: bool, fs: "FileSystemApi"
    ):

        try:
            if append_mode:
                existing_data = fs.read_file(file_path)
                updated_data = existing_data + output.encode()
                fs.edit_file(file_path, updated_data)

            else:
                if not fs.exists(file_path):
                    fs.create_file(file_path, output.encode())
                else:
                    fs.edit_file(file_path, output.encode())

                pass

        except Exception:
            print(f"Error: Unable to write to file '{file_path}'.")

    def get_usage(self) -> str:
        usage = f"Usage: {self.name}"
        for arg in self.arguments:
            if arg.get("optional", False):
                usage += f" [<{arg['name']}>]"
            else:
                usage += f" <{arg['name']}>"
        return usage

    def validate_args(self, args: List[str]):
        required_args = [
            arg for arg in self.arguments if not arg.get("optional", False)
        ]
        if len(args) < len(required_args):
            missing = [arg["name"] for arg in required_args[len(args) :]]
            raise ValueError(f"Missing required arguments: {', '.join(missing)}")
