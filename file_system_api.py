import os
from typing import Any, Dict, List, Optional

from core.file_system import FileSystem
from managers.transaction_manager import TransactionManager
from dataclasses import dataclass
import datetime

from structs.metadata import Metadata


@dataclass(kw_only=True)
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


# @dataclass(kw_only=True)
# class FolderMetadata(FileMetadata):
#     children_count: int

#     def __post_init__(self):
#         super().__post_init__()
#         if not isinstance(self.children_count, int):
#             raise ValueError("children_count should be an integer")


class FileSystemApi:
    """
    This here serves as a handler for all the operations of the file system and should be used when interacting with it.
    """

    FS_PATH = "file_system_disk"

    def __init__(self, user_id: str, file_system: Optional[FileSystem] = None):
        self.user_id = user_id

        if file_system:
            self.file_system = file_system
        else:
            self.file_system = FileSystem(
                file_system_name=f"{FileSystemApi.FS_PATH}/{user_id}.disk"
            )
        self.current_directory = "/"

    @classmethod
    def create_new_file_system(
        cls, user_id: str, metadata: Optional[Dict[str, Any]] = {}
    ) -> "FileSystemApi":
        """
        Creates a new file system and returns an instance of the API.

        :param user_id: The user ID.
        :param metadata: A dictionary containing the metadata.
        :return: An instance of the API.
        """
        file_system = FileSystem(
            file_system_name=f"{FileSystemApi.FS_PATH}/{user_id}.disk",
            specs=Metadata(f"{FileSystemApi.FS_PATH}/{user_id}.disk", **metadata),
        )
        return cls(user_id, file_system=file_system)

    """
    Important Utility Functions.
    """

    def resolve_path(self, path: str) -> str:
        """
        Resolves a given path relative to the current working directory.

        :param path: The path to resolve.
        :return: An absolute path.
        """
        return (
            os.path.join(self.current_directory, path)
            if not os.path.isabs(path)
            else path
        )

    """
    Navigation Operations.
    """

    def change_directory(self, file_path: str) -> None:
        """
        Changes the current working directory to the one specified.

        :param file_path: The path of the directory to change to.
        """
        resolved_path = self.resolve_path(file_path)
        if not self.file_system.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_path}' is not a valid directory.")

        self.current_directory = resolved_path

    def is_valid_path(self, file_path: str) -> bool:
        """
        Checks if the given path is a valid file or directory.

        :param file_path: The path to check.
        :return: True if the path is valid, False otherwise.
        """
        try:
            self.file_system.resolve_path(file_path)
        except Exception:
            return False

        return True

    def exists(self, file_path: str) -> bool:
        """
        Checks if the given path is a valid file or directory.

        :param file_path: The path to check.
        :return: True if the path is valid, False otherwise.
        """
        resolved_path = self.resolve_path(file_path)
        return self.is_valid_path(resolved_path)

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
        resolved_path = self.resolve_path(file_path)

        self.file_system.create_file(resolved_path, file_data)

    def read_file(self, file_path: str) -> bytes:
        """
        Reads and returns the contents of the file at the specified file path.

        :param file_path: The path of the file to be read.
        :return: The contents of the file as bytes.
        """
        resolved_path = self.resolve_path(file_path)
        return self.file_system.read_file(resolved_path)

    def edit_file(self, file_path: str, new_data: bytes) -> None:
        """
        Edits the file at the specified file path with the new data provided.

        :param file_path: The path of the file to be edited.
        :param new_data: The new data to overwrite the existing file content.
        """
        resolved_path = self.resolve_path(file_path)
        self.file_system.edit_file(resolved_path, new_data)

    def delete_file(self, file_path: str) -> None:
        """
        Deletes the file at the specified file path.

        :param file_path: The path of the file to be deleted.
        """
        resolved_path = self.resolve_path(file_path)
        self.file_system.delete_file(resolved_path)

    def rename_file(self, file_path: str, new_name: str) -> None:
        """
        Renames the file at the specified file path to the new name.

        :param file_path: The current path of the file to be renamed.
        :param new_name: The new name for the file.
        """
        resolved_path = self.resolve_path(file_path)
        self.file_system.rename_file(resolved_path, new_name)

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
            file_path=file_path,
            file_size=self.file_system.config_manager.block_size
            * index_node.file_blocks,
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
        resolved_path = self.resolve_path(dir_path)
        files = self.file_system.list_directory_contents(resolved_path)
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
        self.file_system.copy_directory(dir_path, copy_path)

    def get_directory_metadata(self, dir_path: str) -> "FileMetadata":
        """
        Returns a dictionary containing metadata for the given directory.

        :param dir_path: The path of the directory to retrieve metadata for.
        :return: A dictionary containing directory metadata.
        """
        index_node = self.file_system.index_manager.find_file_by_name(dir_path)
        folder_metadata = FileMetadata(
            file_name=index_node.file_name,
            file_path=dir_path,
            file_size=self.file_system.config_manager.block_size * index_node.file_size,
            is_directory=index_node.is_directory,
            children_count=index_node.children_count,
            creation_date=index_node.creation_date,
            modification_date=index_node.modification_date,
        )
        return folder_metadata

    def get_directory_size(self, dir_path: str) -> int:
        """
        Returns the total size of the directory in bytes.

        :param dir_path: The path of the directory to retrieve size for.
        :return: The total size of the directory in bytes.
        """
        return self.file_system.get_file_size(dir_path)

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
