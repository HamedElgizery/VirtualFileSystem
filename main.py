import os
from metadata_utility import (
    Metadata,
)
from file_system import FileSystem


# TODO: VERY IMPORTANT do boundary checks in this case we might as well make an interator for each block (index, bitmap, file_itself)
# TODO: urgently add defragemenation support
# TODO: create more tests
# TODO: use win32 tools to gurrentee support for windows
# TODO: optional add jornaling support and crash recovery
# TODO: optional consider a way to not load entire index into memory and split parts of it (very optional not important at all even)


def file_creation_test(fs: FileSystem):
    # Test: Write and overwrite a file

    file_name = "ahmed_hesham.txt"
    file_data = b"my name is H H"
    fs.create_file(file_name, file_data, "/root")  # Write initial file

    # Overwrite with new data
    # new_file_data = b"my name is H H with extra content"
    # fs.create_file(file_name, new_file_data, "/root")  # Overwrite existing file

    # List all files and print storage details
    for file in fs.list_all_files():
        print(f"File Name: {file.file_name}")
        print(f"File Blocks: {file.file_blocks}")
        print(f"File Start Block: {file.file_start_block}")
        print(f"File Size (in bytes): {file.file_size}")
        print(f"File Content: {fs.read_file(file)}")


def do_fs_tests():
    fs_name = "file.disk"
    if os.path.exists(fs_name):
        os.remove(fs_name)

    if os.path.exists(f"{fs_name}.dt"):
        os.remove(f"{fs_name}.dt")

    config = Metadata(fs_name, 1024 * 1024, 32, 1024 * 1024 * 80, 32)
    fs = FileSystem(fs_name, config)

    for i in range(9):
        file_name = f"file_{i}.txt"
        file_data = b"my name is H H"
        fs.create_file(f"/root/{file_name}", file_data)

    fs.delete_file("/root/file_0.txt")
    fs.defragmentation()
    print(fs.calculate_fragmentation())

    fs.create_directory("/root/a")
    fs.create_directory("/root/a/b")
    fs.create_directory("/root/c")

    dirs = fs.list_directory_contents("/root")
    dirs.sort()
    if dirs[0] != "a" or dirs[1] != "c":
        print("Error in directory creation test")

    dirs = fs.list_directory_contents("/root/a")
    dirs.sort()
    if dirs[0] != "b":
        print("Error in directory creation test")

    file_name = "d"
    file_data = b"my name is H H"
    fs.create_file(f"/root/{file_name}", file_data)
    dirs = fs.list_directory_contents("/root")
    print(fs.read_file(f"/root/{file_name}"))
    fs.edit_file(f"/root/{file_name}", b"this a new life makima my old")
    print(fs.read_file(f"/root/{file_name}"))

    dirs.sort()
    if dirs[0] != "a" or dirs[1] != "c" or dirs[2] != "d":
        print("Error in directory creation test")


if __name__ == "__main__":

    # various tests
    do_fs_tests()

    # Creating new file System

    # name = "file.disk"
    # config = Metadata(name, 4096, 32, 1024 * 1024 * 1, 32)

    # Using pre-existing file system
    # fs = FileSystem("file.disk") # no need to give metadata each time
    # file_creation_test(fs)
