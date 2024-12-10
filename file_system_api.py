from typing import Dict


class FileSystemApi:
    """
    This here serves as a handler for all the operations of the file system and should be used when interacting with it
    """

    def __init__(self):
        pass

    """
    File Operations
    """

    def create_empty_file(self, file_path: str) -> None:
        pass

    def create_file(self, file_path: str, file_data: bytes) -> None:
        pass

    def read_file(self, file_path: str) -> bytes:
        pass

    def edit_file(self, file_path: str, new_data: bytes) -> None:
        pass

    def delete_file(self, file_path: str) -> None:
        pass

    def rename_file(self, file_path: str, new_name: str) -> None:
        pass

    def move_file(self, file_path: str, new_path: str) -> None:
        pass

    def copy_file(self, file_path: str, copy_path: str) -> None:
        pass

    # Will create a simple metadata for each file with timecreated, modification date file size etc

    def get_file_metadata(self, file_path: str):
        pass

    def get_file_size(self, file_path: str):
        pass

    """
    Directory Operations
    """

    def create_directory(self, dir_path: str):
        pass

    def list_directory_contents(self, dir_path: str):
        pass

    def delete_directory(self, dir_path: str):
        pass

    def rename_directory(self, dir_path: str, new_name: str):
        pass

    def move_directory(self, dir_path: str, new_path: str):
        pass

    def copy_directory(self, dir_path: str, copy_path: str):
        pass

    def get_directory_metadata(self, dir_path: str):
        pass

    def get_directory_size(self, dir_path: str):
        pass

    """
    Other Operations
    """

    def search_for_file(self, file_name: str):
        pass

    def get_free_space(self):
        pass

    def get_fragementation_precentage(self):
        pass

    def defragmentation(self):
        pass
