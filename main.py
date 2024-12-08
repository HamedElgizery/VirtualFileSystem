from metadata_utility import Metadata, write_metadata_file, read_metadata_file
from file_system import FileSystem


def file_creation_test(fs: FileSystem):
    # Test: Write and overwrite a file

    file_name = "ahmed_hesham.txt"
    file_data = b"my name is H H"
    fs.create_file(file_name, file_data)  # Write initial file

    # Overwrite with new data
    new_file_data = b"my name is H H with extra content"
    fs.create_file(file_name, new_file_data)  # Overwrite existing file

    # List all files and print storage details
    for file in fs.list_all_files():
        print(f"File Name: {file.file_name}")
        print(f"File Blocks: {file.file_blocks}")
        print(f"File Start Block: {file.file_start_block}")
        print(f"File Size (in bytes): {file.file_size}")
        print(f"File Content: {fs.read_file(file)}")


def directory_creation_test(fs: FileSystem):

    fs.create_directory("ahmed", fs.get_file_by_name("root"))
    print(fs.list_directory_contents("root"))

    # for file in fs.list_all_files():
    #     print(f"File Name: {file.file_name}")


def create_file_system(name: str, specs: Metadata):
    write_metadata_file(name, specs)
    return FileSystem(name, specs)


def load_file_system(name: str):
    specs = read_metadata_file(name)
    return FileSystem(name, specs)


if __name__ == "__main__":
    fs = load_file_system("file.disk")
    directory_creation_test(fs)

    # config = Metadata("file.disk", 4096, 32, 1024 * 1024 * 1, 32)
    # fs = create_file_system("file.disk", config)
