import math
import os
from typing import List, Optional, Union
from file_index_node import FileIndexNode
from index_manager import IndexManager
from metadata_utility import Metadata, MetadataManager
from utility import reset_seek_to_zero
from bitmap_manager import BitmapManager
from config_manager import ConfigManager

# TODO: ensure no 2 file systems are open for the same file
# TODO: ensure new code sepeartion works and try to make use of it


class FileSystem:
    ROOT_DIR = "root"

    def __init__(self, file_system_name: str, specs: Optional[Metadata] = None) -> None:
        if specs:
            self.metedata_manager = MetadataManager(file_system_name, specs)
            self.config_manager = ConfigManager(specs)
        else:
            self.metedata_manager = MetadataManager(file_system_name)
            self.config_manager = ConfigManager(self.metedata_manager.metadata)

        if not os.path.exists(self.config_manager.file_system_path):
            self.fs = open(self.config_manager.file_system_path, "w+b")
        else:
            self.fs = open(self.config_manager.file_system_path, "r+b")

        if os.path.getsize(self.config_manager.file_system_path) == 0:
            self.reserve_file()

        self.bitmap_manager = BitmapManager(
            self.fs, self.config_manager.num_blocks, self.config_manager.block_size
        )
        self.index_manager = IndexManager(self.fs, self.config_manager)

        FileIndexNode.id_generator = lambda: self.metedata_manager.increment_id()

        root = self.index_manager.find_file_by_name(FileSystem.ROOT_DIR)
        if not root:
            root = FileIndexNode(FileSystem.ROOT_DIR, 0, 1, is_directory=True)
            root.id = 0  # id of the root directory is 0
            root.calculate_file_size(self.config_manager.block_size)

            self.bitmap_manager.mark_used(0)
            self.index_manager.write_to_index(root)

    def __del__(self):
        self.fs.close()

    @reset_seek_to_zero
    def load_index(self):
        hash_table = {}
        file_location_map = {}
        for i in range(self.config_manager.max_index_entries):
            self.fs.seek(
                self.config_manager.bitmap_size
                + i * self.config_manager.index_entry_size
            )
            data = self.fs.read(self.config_manager.index_entry_size)
            if data.strip(b"\0") == b"":
                continue

            file_index = FileIndexNode.from_bytes(data, self)
            hash_table[file_index.id] = file_index
            file_location_map[file_index.id] = i

        return hash_table, file_location_map

    # TODO: add a method which will also automically copy all the older blocks and expand
    def realign(self, file_index: FileIndexNode, factor: int = 2) -> None:
        if file_index.is_directory:
            children = file_index.load_children(self)
            self.bitmap_manager.free_block(file_index.file_start_block)

            free_blocks = self.bitmap_manager.find_free_space_bitmap(
                file_index.file_blocks * factor
            )
            start_block = free_blocks[0]

            file_index.file_start_block = start_block
            file_index.file_blocks = len(free_blocks)

            children_data_start = (
                self.config_manager.bitmap_size
                + self.config_manager.file_index_size
                + start_block * self.config_manager.block_size
            )

            for i, child in enumerate(children):
                self.fs.seek(children_data_start + i * 4)
                self.fs.write(child.id.to_bytes(4, byteorder="big"))

            for block in free_blocks:
                self.bitmap_manager.mark_used(block)

        else:
            file_data = self.read_file(file_index)
            self.bitmap_manager.free_block(file_index.file_start_block)

            free_blocks = self.bitmap_manager.find_free_space_bitmap(
                file_index.file_blocks * factor
            )
            start_block = free_blocks[0]

            file_index.file_start_block = start_block
            file_index.file_blocks = len(free_blocks)

            file_data_start = (
                self.config_manager.bitmap_size
                + self.config_manager.file_index_size
                + start_block * self.config_manager.block_size
            )

            self.fs.seek(file_data_start)
            self.fs.write(file_data.ljust(self.config_manager.block_size, b"\0"))

            for block in free_blocks:
                self.bitmap_manager.mark_used(block)

    def delete_file(self, file_dir: str) -> None:
        parent_node, file_node = self.resolve_path(file_dir, True)

        if not file_node:
            raise ValueError("File doesn't exist")
        if file_node.is_directory:
            raise ValueError("Not a file")

        for block in range(file_node.file_blocks):
            self.bitmap_manager.free_block(file_node.file_start_block + block)

        parent_node.remove_child(self, file_node.file_name)
        self.index_manager.delete_from_index(file_node)

    @reset_seek_to_zero
    def reserve_file(self) -> None:
        self.fs.seek(
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + self.config_manager.file_system_size
            - 1
        )
        self.fs.write(b"\0")

    def create_directory(self, dir_name: str):
        # parent_node = self.get_file_by_name(parent_dir_name)
        directories = [d for d in dir_name.split("/") if d not in ("", ".")]
        parent_node = self.resolve_path(directories[-2])
        if not parent_node or not parent_node.is_directory:
            raise Exception("Parent directory does not exist or is not a directory.")
        children = parent_node.load_children(self)
        if any(child.file_name == directories[-1] for child in children):
            raise Exception("Directory already exists.")

        free_block = self.bitmap_manager.find_free_space_bitmap(1)[0]
        self.bitmap_manager.mark_used(free_block)

        new_dir_node = FileIndexNode(
            file_name=directories[-1],
            file_start_block=free_block,
            file_blocks=1,
            is_directory=True,
            children_count=0,
        )
        parent_node.add_child(self, new_dir_node)

        self.index_manager.write_to_index(new_dir_node)
        self.index_manager.write_to_index(parent_node)

    def create_file(self, file_dir: str, file_data: bytes):
        directories = [d for d in file_dir.split("/") if d not in ("", ".")]
        parent_node = self.resolve_path(directories[-2])
        # parent_node = self.get_file_by_name(parent_dir)
        if not parent_node.is_directory:
            raise Exception("Parent directory does not exist or is not a directory.")

        num_blocks_needed = (
            len(file_data) + self.config_manager.block_size - 1
        ) // self.config_manager.block_size
        free_blocks = self.bitmap_manager.find_free_space_bitmap(num_blocks_needed)
        file_start_block_index = free_blocks[0]

        # TODO: later on we will make use of path so for parent_dir it will take a path and we will check files or folders in it to see if name exists or not
        # Check if the file exists
        existing_file = self.index_manager.find_file_by_name(directories[-1])

        if existing_file:
            # Free up the blocks used by the existing file in the bitmap
            for block in range(
                existing_file.file_start_block,
                existing_file.file_start_block + existing_file.file_blocks,
            ):
                self.bitmap_manager.free_block(block)

        # Write the new data to free blocks
        current_offset = 0
        for block in free_blocks:
            self.fs.seek(
                self.config_manager.bitmap_size
                + self.config_manager.file_index_size
                + block * self.config_manager.block_size
            )
            block_data = file_data[
                current_offset : current_offset + self.config_manager.block_size
            ]
            self.fs.write(block_data.ljust(self.config_manager.block_size, b"\0"))
            current_offset += len(block_data)

        # Update bitmap to reflect that these blocks are now used
        for block in free_blocks:
            self.bitmap_manager.mark_used(block)

        # Update the file index
        file_index_node = FileIndexNode(
            file_name=directories[-1],
            file_start_block=file_start_block_index,
            file_blocks=num_blocks_needed,
        )
        file_index_node.calculate_file_size(self.config_manager.block_size)

        parent_node.add_child(self, file_index_node)

        self.index_manager.write_to_index(file_index_node)
        self.index_manager.write_to_index(parent_node)

    # adddED edit file

    def edit_file(self, file_dir: str, new_data: bytes):

        file_node = self.resolve_path(file_dir)

        if not file_node:
            raise FileNotFoundError("File does not exist.")
        if file_node.is_directory:
            raise ValueError("The specified path is a directory.")

        max_data_size = file_node.file_blocks * self.config_manager.block_size
        if len(new_data) > max_data_size:
            self.realign(file_node, len(new_data) // max_data_size)

        start_position = (
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + file_node.file_start_block * self.config_manager.block_size
        )
        self.fs.seek(start_position)
        self.fs.write(new_data.ljust(max_data_size, b"\0"))

    def resolve_path(
        self, path: str, return_parent: bool = False
    ) -> Optional[FileIndexNode]:
        directories = [d for d in path.split("/") if d not in ("", ".")]
        current_id = 0 if path.startswith("/") else self.index_manager.index[0].id
        parent_id = 0 if path.startswith("/") else self.index_manager.index[0].id

        for i, directory in enumerate(directories):

            if directory == "" or directory == ".":
                continue

            if len(directories) == 1 and directory == FileSystem.ROOT_DIR:
                return self.index_manager.index[current_id]

            if i == 0 and directory == FileSystem.ROOT_DIR:
                continue

            if directory == "..":
                parent_id = current_id
                parent_dir = self.index_manager.index[current_id]
                current_id = parent_dir.id
                continue

            for child in self.index_manager.index[current_id].load_children(self):
                if child.file_name == directory:
                    parent_id = current_id
                    current_id = child.id
                    break
            else:
                raise FileNotFoundError(f"File {directory} not found.")

        if return_parent:
            return (
                self.index_manager.index[parent_id],
                self.index_manager.index[current_id],
            )

        return self.index_manager.index[current_id]

    @reset_seek_to_zero
    def list_all_files(self) -> List[FileIndexNode]:
        return list(self.index_manager.index.values())

    def list_directory_contents(self, dir_name: str) -> List[str]:
        # dir_node = self.get_file_by_name(dir_name)
        dir_node = self.resolve_path(dir_name)
        if not dir_node or not dir_node.is_directory:
            raise Exception("Directory does not exist or is not a directory.")

        children = dir_node.load_children(self)
        return [child.file_name for child in children]

    # TODO: i need to centralize this shit i dont want some to work like this and some to work like that but oh well
    @reset_seek_to_zero
    def read_file(self, file_dir: Union[str, FileIndexNode]) -> bytes:
        if isinstance(file_dir, str):
            file_node = self.resolve_path(file_dir)
        elif isinstance(file_dir, FileIndexNode):
            file_node = file_dir
        else:
            raise ValueError("File dir must be a str or FileIndexNode")
        self.fs.seek(
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + file_node.file_start_block * self.config_manager.block_size
        )
        data = []

        for i in range(file_node.file_blocks):
            data.append(self.fs.read(self.config_manager.block_size))
            self.fs.seek(
                self.config_manager.bitmap_size
                + self.config_manager.file_index_size
                + file_node.file_start_block * self.config_manager.block_size
                + i * self.config_manager.block_size
            )

        return b"".join(data).rstrip(b"\x00")

    def find_file_by_name(self, file_name: str) -> Optional[FileIndexNode]:
        for file_index in self.index_manager.index.values():
            if file_index.file_name == file_name:
                return file_index

        return None

    def rename_file(self, old_dir: str, new_name: str) -> None:
        file_node = self.resolve_path(old_dir)
        if not file_node:
            raise FileNotFoundError(f"File '{old_dir}' not found.")

        file_node.file_name = new_name

        self.index_manager.write_to_index(file_node)

    def copy_file(self, old_dir: str, new_dir: str) -> None:
        file_node = self.resolve_path(old_dir)
        if not file_node:
            raise FileNotFoundError(f"File '{old_dir}' not found.")

        self.create_file(new_dir, self.read_file(old_dir))

    def move_file(self, old_dir: str, new_dir: str) -> None:
        file_node = self.resolve_path(old_dir)
        if not file_node:
            raise FileNotFoundError(f"File '{old_dir}' not found.")

        self.copy_file(old_dir, new_dir)
        self.delete_file(old_dir)

    def calculate_fragmentation(self):
        # Sort the file nodes by start block
        file_nodes = sorted(
            self.index_manager.index.values(), key=lambda node: node.file_start_block
        )

        total_free_in_gaps = 0

        # Iterate through sorted files to calculate gaps
        for i in range(len(file_nodes) - 1):
            current_file = file_nodes[i]
            next_file = file_nodes[i + 1]

            # Calculate the end block of the current file
            current_end_block = (
                current_file.file_start_block + current_file.file_blocks - 1
            )

            # Calculate the gap between the current file and the next file
            gap = next_file.file_start_block - current_end_block - 1
            if gap > 0:
                total_free_in_gaps += gap

        # Get the block number of the last file's last block
        if file_nodes:
            last_file = file_nodes[-1]
            last_end_block = last_file.file_start_block + last_file.file_blocks - 1
        else:
            last_end_block = 0  # No files, so no fragmentation

        # Calculate fragmentation percentage only up to the last used block
        fragmentation_percentage = (total_free_in_gaps / (last_end_block + 1)) * 100
        return fragmentation_percentage

    # TODO: do this shit tomorrow
    def defragmentation(self):

        file_nodes = sorted(
            self.index_manager.index.values(), key=lambda node: node.file_start_block
        )

        for node in file_nodes:
            pass
