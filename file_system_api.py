import logging
import os
import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.file_system import FileSystem
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

        self.logger = logging.getLogger(self.user_id)

        if file_system:
            self.file_system = file_system
        else:
            self.file_system = FileSystem(
                file_system_name=f"{FileSystemApi.FS_PATH}/{user_id}",
                user_id=self.user_id,
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
            file_system_name=f"{FileSystemApi.FS_PATH}/{user_id}",
            specs=Metadata(f"{FileSystemApi.FS_PATH}/{user_id}.disk", **metadata),
            user_id=user_id,
        )
        return cls(user_id, file_system=file_system)

    @classmethod
    def file_system_exists(cls, user_id: str) -> bool:
        """
        Checks if a file system exists.

        :param user_id: The user ID.
        :return: True if the file system exists, False otherwise.
        """
        return os.path.exists(f"{FileSystemApi.FS_PATH}/{user_id}.disk")

    # Important Utility Functions.

    def normalize_path(self, path: str) -> str:
        """Normalize the path and replace the separator with '/'.

        :param path: The path to normalize.
        :return: A normalized path.
        """
        # Replace the separator with '/' and normalize the path
        return os.path.join(self.current_directory, path).replace(os.sep, "/")

    def resolve_path(self, path: str) -> str:
        """
        Resolves a given path relative to the current working directory.
        Handles special cases like ., .., /., ./, and multiple slashes (e.g., ////).

        :param path: The path to resolve.
        :return: An absolute, normalized path.
        """
        if path in ["", ".", "./"]:
            # Current directory
            return self.current_directory
        if path == "..":
            # Parent directory
            return os.path.dirname(self.current_directory)
        if path.startswith("./"):
            # Strip the leading ./ and resolve relative to the current directory
            path = path[2:]
        elif path.startswith("/."):
            # Normalize /. and resolve as an absolute path
            path = "/" + path[2:]
        elif path.startswith("//"):
            # Simplify multiple leading slashes
            path = "/" + path.lstrip("/")

        # Normalize the combined path
        resolved_path = (
            os.path.join(self.current_directory, path)
            if not os.path.isabs(path)
            else path
        )
        return self.normalize_path(os.path.normpath(resolved_path))

    # Navigation Operations.

    def change_directory(self, file_path: str) -> None:
        """
        Changes the current working directory to the one specified.

        :param file_path: The path of the directory to change to.
        """
        resolved_path = self.resolve_path(file_path)
        if not self.file_system.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_path}' is not a valid directory.")

        self.logger.info("Changed directory to %s", resolved_path)
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

    def is_directory(self, file_path: str) -> bool:
        """
        Checks if the given path is a directory.

        :param file_path: The path to check.
        :return: True if the path is a directory, False otherwise.
        """
        resolved_path = self.resolve_path(file_path)
        return self.file_system.is_directory(resolved_path)

    def exists(self, file_path: str) -> bool:
        """
        Checks if the given path is a valid file or directory.

        :param file_path: The path to check.
        :return: True if the path is valid, False otherwise.
        """
        resolved_path = self.resolve_path(file_path)
        return self.is_valid_path(resolved_path)

    # File Operations.

    def create_empty_file(self, file_path: str) -> None:
        """
        Creates an empty file at the specified file path.

        :param file_path: The path where the new empty file will be created.
        """
        resolved_path = self.resolve_path(file_path)
        self.file_system.create_file(resolved_path, b"")
        self.logger.info("Created empty file at %s", resolved_path)

    def create_file(self, file_path: str, file_data: bytes) -> None:
        """
        Creates a new file with the given data at the specified file path.

        :param file_path: The path where the new file will be created.
        :param file_data: The data to be written to the new file.
        """
        if type(file_data) is not bytes:
            raise ValueError("new_data must be of type bytes")

        resolved_path = self.resolve_path(file_path)
        self.file_system.create_file(resolved_path, file_data)
        self.logger.info(
            "Created new file at %s with data of length %d",
            resolved_path,
            len(file_data),
        )

    def read_file(self, file_path: str) -> bytes:
        """
        Reads and returns the contents of the file at the specified file path.

        :param file_path: The path of the file to be read.
        :return: The contents of the file as bytes.
        """
        if self.is_directory(file_path):
            raise ValueError(f"The path '{file_path}' is a directory.")

        resolved_path = self.resolve_path(file_path)
        data = self.file_system.read_file(resolved_path)
        self.logger.info(f"Read {resolved_path} with data of length {len(data)}")
        return data

    def edit_file(self, file_path: str, new_data: bytes) -> None:
        """
        Edits the file at the specified file path with the new data provided.

        :param file_path: The path of the file to be edited.
        :param new_data: The new data to overwrite the existing file content.
        """
        if self.is_directory(file_path):
            raise ValueError(f"The path '{file_path}' is a directory.")

        if type(new_data) is not bytes:
            raise ValueError("new_data must be of type bytes")

        resolved_path = self.resolve_path(file_path)
        self.file_system.edit_file(resolved_path, new_data)
        self.logger.info(
            f"Edited {resolved_path} with new data of length {len(new_data)}"
        )

    def delete_file(self, file_path: str) -> None:
        """
        Deletes the file at the specified file path.

        :param file_path: The path of the file to be deleted.
        """
        resolved_path = self.resolve_path(file_path)

        if self.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_path}' is a directory.")

        self.file_system.delete_file(resolved_path)
        self.logger.info(f"Deleted {resolved_path}")

    def rename_file(self, file_path: str, new_name: str) -> None:
        """
        Renames the file at the specified file path to the new name.

        :param file_path: The current path of the file to be renamed.
        :param new_name: The new name for the file.
        """
        resolved_path = self.resolve_path(file_path)
        self.file_system.rename_file(resolved_path, new_name)
        self.logger.info(f"Renamed {resolved_path} to {new_name}")

    def move_file(self, file_path: str, new_path: str) -> None:
        """
        Moves the file from the specified file path to a new path.

        :param file_path: The current path of the file to be moved.
        :param new_path: The new path where the file will be moved.
        """
        resolved_path = self.resolve_path(file_path)
        resolved_output_path = self.resolve_path(new_path)
        resolved_output_path = self.normalize_path(
            os.path.join(resolved_output_path, os.path.basename(file_path))
        )

        self.file_system.move_file(resolved_path, resolved_output_path)
        self.logger.info(f"Moving {file_path} to {new_path}")

    def copy_file(self, file_path: str, copy_path: str) -> None:
        """
        Copies the file from the specified file path to a new path.

        :param file_path: The current path of the file to be copied.
        :param copy_path: The path where the file will be copied to.
        """
        resolved_path = self.resolve_path(file_path)
        resolved_output_path = self.resolve_path(copy_path)

        resolved_output_path = self.normalize_path(
            os.path.join(resolved_output_path, os.path.basename(file_path))
        )

        if self.is_directory(resolved_output_path) or self.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_output_path}' is a directory.")

        self.file_system.copy_file(resolved_path, resolved_output_path)
        self.logger.info(f"Copied {resolved_path} to {resolved_output_path}")

    # Will create a simple metadata for each file with timecreated, modification date file size etc

    def get_file_metadata(self, file_path: str) -> "FileMetadata":
        """
        Returns a dictionary containing metadata for the given file.

        :param file_path: The path of the file to retrieve metadata for.
        :return: A dictionary containing file metadata.
        """
        resolved_path = self.resolve_path(file_path)
        index_node = self.file_system.resolve_path(resolved_path)
        file_metadata = FileMetadata(
            file_name=index_node.file_name,
            file_path=resolved_path,
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
        resolved_path = self.resolve_path(file_path)

        if self.is_directory(file_path):
            raise ValueError("Cannot get size of a directory.")

        return self.file_system.get_file_size(resolved_path)

    """
    Directory Operations.
    """

    def create_directory(self, dir_path: str) -> None:
        """
        Creates a new directory in the filesystem.

        :param dir_path: The path of the new directory to create.
        """
        resolved_path = self.resolve_path(dir_path)
        self.file_system.create_directory(resolved_path)

    def list_directory_contents(self, dir_path: str) -> List[str]:
        """
        Returns a list of the contents of the given directory.

        :param dir_path: The path of the directory to list contents for.
        :return: A list of the contents of the given directory.
        """
        resolved_path = self.resolve_path(dir_path)

        if not self.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_path}' is not a directory.")

        files = self.file_system.list_directory_contents(resolved_path)
        return files

    def delete_directory(self, dir_path: str) -> None:
        """
        Deletes a directory in the filesystem.

        :param dir_path: The path of the directory to delete.
        """
        resolved_path = self.resolve_path(dir_path)

        if not self.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_path}' is not a directory.")

        self.file_system.delete_directory(resolved_path)

    def rename_directory(self, dir_path: str, new_name: str) -> None:
        """
        Renames a directory in the filesystem.

        :param dir_path: The current path of the directory to be renamed.
        :param new_name: The new name for the directory.
        """
        resolved_path = self.resolve_path(dir_path)
        self.file_system.rename_file(resolved_path, new_name)

    def move_directory(self, dir_path: str, new_path: str) -> None:
        """
        Moves a directory in the filesystem.

        :param dir_path: The current path of the directory to be moved.
        :param new_path: The new path where the directory will be moved.
        """
        resolved_path = self.resolve_path(dir_path)
        resolved_output_path = self.resolve_path(new_path)
        resolved_output_path = self.normalize_path(
            os.path.join(resolved_output_path, os.path.basename(new_path))
        )
        self.file_system.move_file(resolved_path, resolved_output_path)

    def copy_directory(self, dir_path: str, copy_path: str) -> None:
        """
        Copies a directory in the filesystem.

        :param dir_path: The current path of the directory to be copied.
        :param copy_path: The path where the directory will be copied to.
        """
        resolved_path = self.resolve_path(dir_path)
        resolved_output_path = self.resolve_path(copy_path)

        resolved_output_path = self.normalize_path(
            os.path.join(resolved_output_path, os.path.basename(dir_path))
        )

        if self.is_directory(resolved_output_path) or self.is_directory(resolved_path):
            raise ValueError(f"The path '{resolved_output_path}' is a directory.")

        self.file_system.copy_directory(resolved_path, resolved_output_path)

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
        resolved_path = self.resolve_path(dir_path)
        return self.file_system.get_file_size(resolved_path)

    def make_directories(self, dir_path: str):
        """
        Will recursivally create all the directories in the path
        """
        resolved_path = self.resolve_path(dir_path)
        split_path = resolved_path.split("/")
        processed_path = "/"

        for path in split_path:
            processed_path = self.normalize_path(os.path.join(processed_path, path))
            if self.exists(processed_path) and self.is_directory(processed_path):
                continue
            self.file_system.create_directory(processed_path)

    """
    Other Operations.
    """

    def search_for_file(self, file_name: str) -> List[str]:
        """
        Searches for a file in the entire filesystem and returns a list of paths
        where the file was found.

        :param file_name: The name of the file to search for.
        :return: A list of paths where the file was found.
        """
        pass

    def get_free_space(self) -> int:
        """
        Returns the total amount of free space in the filesystem in bytes.

        :return: The total amount of free space in the filesystem in bytes.
        """
        pass

    def get_fragementation_precentage(self) -> float:
        """
        Calculates the percentage of free space that is fragmented.

        :return: The percentage of free space that is fragmented.
        """
        return self.get_fragementation_precentage()

    def defragmentation(self) -> None:
        """
        Defragments the filesystem. This is a blocking operation and will take a
        long time for large filesystems.
        """
        pass
