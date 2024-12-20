import os
import shutil
import uuid
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from core.file_system import FileSystem
from structs.metadata import Metadata
from file_system_api import FileSystemApi, FileMetadata


@pytest.fixture
def file_system_api():
    """Initialize the FileSystemApi with a real file system."""
    user_id = str(uuid.uuid4())
    if FileSystemApi.file_system_exists(user_id):
        os.remove(f"{FileSystemApi.FS_PATH}/test_user.disk")
        os.remove(f"{FileSystemApi.FS_PATH}/test_user.disk.dt")

    return FileSystemApi.create_new_file_system(user_id=user_id)


def test_create_empty_file(file_system_api):
    file_path = "test_file.txt"

    # Create an empty file
    file_system_api.create_empty_file(file_path)

    # Check that the file exists
    assert file_system_api.exists(file_path)
    assert not file_system_api.is_directory(file_path)


def test_read_file(file_system_api):
    file_path = "test_file.txt"

    # Create and read a file
    file_system_api.create_file(file_path, b"Hello, World!")
    data = file_system_api.read_file(file_path)

    # Check that the file contents match
    assert data == b"Hello, World!"


def test_get_file_metadata(file_system_api):
    file_path = "test_file.txt"

    # Create a file and retrieve its metadata
    file_system_api.create_file(file_path, b"Metadata test")
    metadata = file_system_api.get_file_metadata(file_path)

    # Validate metadata
    assert metadata.file_name == "test_file.txt"
    assert metadata.is_directory is False
