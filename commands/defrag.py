from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class DefragCommand(BaseCommand):
    """
    Simulates the behavior of the 'mkdir' command to create a directory.

    Usage:
      mkdir <directory_name>
    """

    name = "defrag"
    description = "Creates a directory."
    arguments = []

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        print("Before: " + str(fs.get_fragmentation_percentage()))
        fs.defragmentation()
        print("After: " + str(fs.get_fragmentation_percentage()))
        return "Defragmentation done succesfully!"
