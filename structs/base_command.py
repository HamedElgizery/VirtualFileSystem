from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Dict, Any

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
    def execute(self, args: List[str], fs: "FileSystemApi"):
        pass

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
