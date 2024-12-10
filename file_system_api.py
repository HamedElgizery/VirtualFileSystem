from typing import Any, Dict, List, Optional

from core.file_system import FileSystem
from transaction_manager import TransactionManager
from dataclasses import dataclass
import datetime


@dataclass
class FileMetadata:
    file_name: str
    file_path: str
    file_size: int
    is_directory: bool
    children_count: Optional[int] = 0
    creation_date: Optional[datetime.datetime] = None
    modification_date: Optional[datetime.datetime] = None

    def __post_init__(self):
        """
        Ensures that creation and modification dates are datetime objects.
        """
        if isinstance(self.creation_date, int):
            self.creation_date = datetime.datetime.fromtimestamp(self.creation_date)
        if isinstance(self.modification_date, int):
            self.modification_date = datetime.datetime.fromtimestamp(
                self.modification_date
            )


class FileSystemApi:
    """
    This here serves as a handler for all the operations of the file system and should be used when interacting with it.
    """

    def __init__(self, user_id: str):
        self.file_system = FileSystem(file_system_name=f"{user_id}_fs")

    """
    File Operations.
    """

    def create_empty_file(self, file_path: str) -> None:
        """
        Creates an empty file at the specified file path.

        :param file_path: The path where the new empty file will be created.
        """
        self.file_system.create_file(file_path, b"")

    def create_file(self, file_path: str, file_data: bytes) -> None:
        """
        Creates a new file with the given data at the specified file path.

        :param file_path: The path where the new file will be created.
        :param file_data: The data to be written to the new file.
        """
        self.file_system.create_file(file_path, file_data)

    def read_file(self, file_path: str) -> bytes:
        """
        Reads and returns the contents of the file at the specified file path.

        :param file_path: The path of the file to be read.
        :return: The contents of the file as bytes.
        """
        return self.file_system.read_file(file_path)

    def edit_file(self, file_path: str, new_data: bytes) -> None:
        """
        Edits the file at the specified file path with the new data provided.

        :param file_path: The path of the file to be edited.
        :param new_data: The new data to overwrite the existing file content.
        """
        self.file_system.edit_file(file_path, new_data)

    def delete_file(self, file_path: str) -> None:
        """
        Deletes the file at the specified file path.

        :param file_path: The path of the file to be deleted.
        """
        self.file_system.delete_file(file_path)

    def rename_file(self, file_path: str, new_name: str) -> None:
        """
        Renames the file at the specified file path to the new name.

        :param file_path: The current path of the file to be renamed.
        :param new_name: The new name for the file.
        """
        self.file_system.rename_file(file_path, new_name)

    def move_file(self, file_path: str, new_path: str) -> None:
        """
        Moves the file from the specified file path to a new path.

        :param file_path: The current path of the file to be moved.
        :param new_path: The new path where the file will be moved.
        """
        self.file_system.move_file(file_path, new_path)

    def copy_file(self, file_path: str, copy_path: str) -> None:
        """
        Copies the file from the specified file path to a new path.

        :param file_path: The current path of the file to be copied.
        :param copy_path: The path where the file will be copied to.
        """
        self.file_system.copy_file(file_path, copy_path)

    # Will create a simple metadata for each file with timecreated, modification date file size etc

    def get_file_metadata(self, file_path: str) -> "FileMetadata":
        """
        Returns a dictionary containing metadata for the given file.

        :param file_path: The path of the file to retrieve metadata for.
        :return: A dictionary containing file metadata.
        """
        index_node = self.file_system.index_manager.find_file_by_name(file_path)
        file_metadata = FileMetadata(
            file_name=index_node.file_name,
            file_path=index_node.file_path,
            file_size=index_node.file_size,
            is_directory=index_node.is_directory,
            children_count=index_node.children_count,
            creation_date=index_node.creation_date,
            modification_date=index_node.modification_date,
        )
        return file_metadata

    def get_file_size(self, file_path: str) -> int:
        """
        Returns the size of the file in bytes.

        :param file_path: The path of the file to retrieve size for.
        :return: The size of the file in bytes.
        """
        return self.file_system.get_file_size(file_path)

    """
    Directory Operations.
    """

    def create_directory(self, dir_path: str) -> None:
        """
        Creates a new directory in the filesystem.

        :param dir_path: The path of the new directory to create.
        """
        self.file_system.create_directory(dir_path)

    def list_directory_contents(self, dir_path: str) -> List[str]:
        """
        Returns a list of the contents of the given directory.

        :param dir_path: The path of the directory to list contents for.
        :return: A list of the contents of the given directory.
        """
        files = self.file_system.list_directory_contents(dir_path)
        return files

    def delete_directory(self, dir_path: str) -> None:
        """
        Deletes a directory in the filesystem.

        :param dir_path: The path of the directory to delete.
        """
        self.file_system.delete_directory(dir_path)

    def rename_directory(self, dir_path: str, new_name: str) -> None:
        """
        Renames a directory in the filesystem.

        :param dir_path: The current path of the directory to be renamed.
        :param new_name: The new name for the directory.
        """
        self.file_system.rename_file(dir_path, new_name)

    def move_directory(self, dir_path: str, new_path: str) -> None:
        """
        Moves a directory in the filesystem.

        :param dir_path: The current path of the directory to be moved.
        :param new_path: The new path where the directory will be moved.
        """
        self.file_system.move_file(dir_path, new_path)

    def copy_directory(self, dir_path: str, copy_path: str) -> None:
        """
        Copies a directory in the filesystem.

        :param dir_path: The current path of the directory to be copied.
        :param copy_path: The path where the directory will be copied to.
        """
        pass

    def get_directory_metadata(self, dir_path: str) -> Dict[str, Any]:
        """
        Returns a dictionary containing metadata for the given directory.

        :param dir_path: The path of the directory to retrieve metadata for.
        :return: A dictionary containing directory metadata.
        """
        pass

    def get_directory_size(self, dir_path: str) -> int:
        """
        Returns the total size of the directory in bytes.

        :param dir_path: The path of the directory to retrieve size for.
        :return: The total size of the directory in bytes.
        """
        pass

    """
    Other Operations.
    """

    def search_for_file(self, file_name: str):
        pass

    def get_free_space(self):
        pass

    def get_fragementation_precentage(self):
        pass

    def defragmentation(self):
        pass

    """
    Custom Rollbacks.
    """
