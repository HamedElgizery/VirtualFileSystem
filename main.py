from metadata_utility import (
    Metadata,
)
from file_system import FileSystem


# TODO: make sure to have path resolultion to be able to write files or other directories to nested directories


def file_creation_test(fs: FileSystem):
    # Test: Write and overwrite a file

    file_name = "ahmed_hesham.txt"
    file_data = b"my name is H H"
    fs.create_file(file_name, file_data, "root")  # Write initial file

    # Overwrite with new data
    # new_file_data = b"my name is H H with extra content"
    # fs.create_file(file_name, new_file_data, "root")  # Overwrite existing file

    # List all files and print storage details
    for file in fs.list_all_files():
        print(f"File Name: {file.file_name}")
        print(f"File Blocks: {file.file_blocks}")
        print(f"File Start Block: {file.file_start_block}")
        print(f"File Size (in bytes): {file.file_size}")
        print(f"File Content: {fs.read_file(file)}")


def directory_creation_test(fs: FileSystem):
    fs.create_directory("ahmed30", "root")
    print(fs.list_directory_contents("root"))


if __name__ == "__main__":

    name = "file.disk"
    config = Metadata(name, 4096, 32, 1024 * 1024 * 1, 32)

    # Creating new file System

    fs = FileSystem(name, config)

    # directory creation test

    fs = FileSystem(name)
    directory_creation_test(fs)
