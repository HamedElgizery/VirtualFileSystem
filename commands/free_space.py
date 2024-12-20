from typing import TYPE_CHECKING, List
from structs.base_command import BaseCommand

if TYPE_CHECKING:
    from file_system_api import FileSystemApi


class FreeSpace(BaseCommand):
    """
    Get the free space in disk out of total space in MB.
    """

    name = "free_space"
    description = "Get the free space in disk out of total space in MB"
    arguments = [
        {"name": "precentage", "optional": True},
    ]

    def execute(self, args: List[str], file_system: "FileSystemApi") -> List[str]:
        use_precentage = "-p" in args

        total_space = file_system.get_total_space() / (1024)
        free_space = file_system.get_free_space() / (1024)
        if use_precentage:
            free_space = (free_space / total_space) * 100
            return f"{free_space:.2f}/100 %"

        return f"{free_space:.2f} KB / {total_space:.2f} KB"
