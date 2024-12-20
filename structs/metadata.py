"""
Module containing the Metadata class. This class is used to store the metadata
of the file system.
"""

from dataclasses import dataclass


@dataclass
class Metadata:
    """
    Class representing the metadata of the file system.

    Attributes:
        file_system_path (str): The path of the file system.
        file_index_size (int): The size of the file index in bytes. Defaults to
            2MB.
        block_size (int): The size of each block in bytes. Defaults to 32 bytes.
        file_system_size (int): The size of the file system in bytes. Defaults to
            80MB.
        file_name_size (int): The size of each file name in bytes. Defaults to 36
            bytes.
        current_id (int): The current id of the metadata. Defaults to 1.
    """

    file_system_path: str
    file_index_size: int = 1024 * 1024 * 2
    block_size: int = 32
    file_system_size: int = 1024 * 1024 * 80
    file_name_size: int = 36
    current_id: int = 1
