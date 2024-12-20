from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class CalcFragCommand(BaseCommand):
    """
    Calculates the fragementation %
    """

    name = "calc_frag"
    description = "Calculates Fragmentation %"
    arguments = []

    def execute(self, args: List[str], fs: "FileSystemApi") -> str:
        return str(fs.get_fragmentation_percentage())
