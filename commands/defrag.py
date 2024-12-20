from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class DefragCommand(BaseCommand):
    """
    Defragments the disk
    """

    name = "defrag"
    description = "Fragments the disk"
    arguments = []

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        output = ""
        output += "Before: " + str(fs.get_fragmentation_percentage()) + "\n"
        fs.defragmentation()
        output += "After: " + str(fs.get_fragmentation_percentage()) + "\n"
        output += "Defragmentation done succesfully!"
        return output
