import math
import os
from typing import List, Optional
from file_index_node import FileIndexNode
from metadata_utility import Metadata
from utility import reset_seek_to_zero


class FileSystem:
    def __init__(self, file_system_name: str, specs: Metadata) -> None:
        self.set_config(specs)
        self.FILE_SYSTEM_PATH = file_system_name
        if not os.path.exists(self.FILE_SYSTEM_PATH):
            self.fs = open(self.FILE_SYSTEM_PATH, "w+b")
        else:
            self.fs = open(self.FILE_SYSTEM_PATH, "r+b")

        if os.path.getsize(self.FILE_SYSTEM_PATH) == 0:
            self.reserve_file()

        self.current_page = None
        self.current_page_index = 0
        self.bitmap = self.load_bitmap()
        self.index, self.index_locations = self.load_index()

        root = self.get_file_by_name("root")
        if not root:
            root = FileIndexNode("root", 0, 1, is_directory=True)
            root.id = 0  # id of the root directory is 0
            root.calculate_file_size(self.BLOCK_SIZE)
            self.write_to_index(root)

    def __del__(self):
        if not self.fs.closed:
            self.fs.close()

    def set_config(self, specs: Metadata):
        self.FILE_SYSTEM_PATH = specs.file_system_path
        self.FILE_INDEX_SIZE = specs.file_index_size
        self.BLOCK_SIZE = specs.block_size
        self.FILE_SYSTEM_SIZE = specs.file_system_size
        self.FILE_NAME_SIZE = specs.file_name_size
        self.NUM_BLOCKS = specs.file_system_size // specs.block_size
        self.MAX_FILE_BLOCKS = math.ceil(math.log2(self.NUM_BLOCKS) / 8)
        self.FILE_START_BLOCK_INDEX_SIZE = self.MAX_FILE_BLOCKS
        self.MAX_LENGTH_CHILDRENS = self.FILE_START_BLOCK_INDEX_SIZE
        self.INDEX_ENTRY_SIZE = (
            4
            + self.FILE_NAME_SIZE
            + self.MAX_FILE_BLOCKS
            + self.FILE_START_BLOCK_INDEX_SIZE
            + 1
            + self.MAX_LENGTH_CHILDRENS
            + self.FILE_START_BLOCK_INDEX_SIZE
        )
        self.MAX_INDEX_ENTRIES = self.FILE_INDEX_SIZE // self.INDEX_ENTRY_SIZE
        self.BITMAP_SIZE = self.NUM_BLOCKS // 8

    @reset_seek_to_zero
    def reserve_file(self) -> None:
        self.fs.seek(
            self.BITMAP_SIZE + self.FILE_INDEX_SIZE + self.FILE_SYSTEM_SIZE - 1
        )
        self.fs.write(b"\0")

    @reset_seek_to_zero
    def load_bitmap(self) -> bytearray:
        return bytearray(self.fs.read(self.BITMAP_SIZE))

    @reset_seek_to_zero
    def load_index(self):
        hash_table = {}
        file_location_map = {}
        for i in range(self.MAX_INDEX_ENTRIES):
            self.fs.seek(self.BITMAP_SIZE + i * self.INDEX_ENTRY_SIZE)
            data = self.fs.read(self.INDEX_ENTRY_SIZE)
            if data.strip(b"\0") == b"":
                continue

            file_index = FileIndexNode.from_bytes(data, self)
            hash_table[file_index.id] = file_index
            file_location_map[file_index.id] = i

        return hash_table, file_location_map

    def create_directory(self, dir_name: str, parent_node: FileIndexNode = None):
        # parent_node = self.get_file_by_name(parent_dir_name)
        if not parent_node or not parent_node.is_directory:
            raise Exception("Parent directory does not exist or is not a directory.")

        if any(child.file_name == dir_name for child in parent_node.children):
            raise Exception("Directory already exists.")

        free_blocks = self.find_free_space_bitmap(1)

        new_dir_node = FileIndexNode(
            file_name=dir_name,
            file_start_block=free_blocks[0],
            file_blocks=1,
            is_directory=True,
            children_count=0,
        )
        parent_node.children.append(new_dir_node)
        parent_node.children_count += 1

        parent_node.save_children(
            self.fs, self.BLOCK_SIZE, self, lambda x: self.find_free_space_bitmap(x)
        )

        self.write_to_index(new_dir_node)
        self.write_to_index(parent_node)

    def create_file(self, file_name: str, file_data: bytes):
        num_blocks_needed = (len(file_data) + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
        free_blocks = self.find_free_space_bitmap(num_blocks_needed)
        file_start_block_index = free_blocks[0]

        # Check if the file exists
        existing_file = self.get_file_by_name(file_name)

        if existing_file:
            # Free up the blocks used by the existing file in the bitmap
            for block in range(
                existing_file.file_start_block,
                existing_file.file_start_block + existing_file.file_blocks,
            ):
                byte_index = block // 8
                bit_index = block % 8
                self.bitmap[byte_index] &= ~(1 << bit_index)
                self.update_bitmap(byte_index)

        # Write the new data to free blocks
        current_offset = 0
        for block in free_blocks:
            self.fs.seek(
                self.BITMAP_SIZE + self.FILE_INDEX_SIZE + block * self.BLOCK_SIZE
            )
            block_data = file_data[current_offset : current_offset + self.BLOCK_SIZE]
            self.fs.write(block_data.ljust(self.BLOCK_SIZE, b"\0"))
            current_offset += len(block_data)

        # Update bitmap to reflect that these blocks are now used
        for block in free_blocks:
            byte_index = block // 8
            bit_index = block % 8
            self.bitmap[byte_index] |= 1 << bit_index
            self.update_bitmap(byte_index)

        # Update the file index
        file_index_node = FileIndexNode(
            file_name=file_name,
            file_start_block=file_start_block_index,
            file_blocks=num_blocks_needed,
        )
        file_index_node.calculate_file_size(self.BLOCK_SIZE)
        self.write_to_index(file_index_node)

    @reset_seek_to_zero
    def update_bitmap(self, byte_index) -> None:
        self.fs.seek(byte_index)
        self.fs.write(bytes([self.bitmap[byte_index]]))

    def find_free_space_bitmap(self, required_blocks: int):
        free_blocks = []

        for i in range(self.NUM_BLOCKS):
            byte_index = i // 8
            bit_index = i % 8

            if not self.bitmap[byte_index] & (1 << bit_index):
                free_blocks.append(i)
                if len(free_blocks) == required_blocks:
                    break

        if len(free_blocks) < required_blocks:
            raise Exception("No free space available.")

        return free_blocks

    @reset_seek_to_zero
    def write_to_index(self, file_index: FileIndexNode) -> None:
        if len(file_index.file_name) > self.FILE_NAME_SIZE:
            raise ValueError("File name too long.")

        if file_index.id in self.index:
            self.index[file_index.id] = file_index

            self.fs.seek(
                self.BITMAP_SIZE
                + self.index_locations[file_index.id] * self.INDEX_ENTRY_SIZE
            )
            self.fs.write(
                file_index.to_bytes(
                    self.FILE_NAME_SIZE,
                    self.MAX_FILE_BLOCKS,
                    self.FILE_START_BLOCK_INDEX_SIZE,
                    self.MAX_LENGTH_CHILDRENS,
                )
            )
            return

        self.index[file_index.id] = file_index

        for i in range(self.MAX_INDEX_ENTRIES):
            self.fs.seek(self.BITMAP_SIZE + i * self.INDEX_ENTRY_SIZE)
            data = self.fs.read(self.INDEX_ENTRY_SIZE)
            if data.strip(b"\0") != b"":
                continue

            # Update the file index
            self.fs.seek(self.BITMAP_SIZE + i * self.INDEX_ENTRY_SIZE)
            self.fs.write(
                file_index.to_bytes(
                    self.FILE_NAME_SIZE,
                    self.MAX_FILE_BLOCKS,
                    self.FILE_START_BLOCK_INDEX_SIZE,
                    self.MAX_LENGTH_CHILDRENS,
                )
            )
            self.index[file_index.id] = file_index
            self.index_locations[file_index.id] = i

            return

        raise Exception("No space in file index.")

    @reset_seek_to_zero
    def list_all_files(self) -> List[FileIndexNode]:
        return list(self.index.values())

        # files = []

        # for i in range(self.MAX_INDEX_ENTRIES):
        #     self.fs.seek(self.BITMAP_SIZE + i * self.INDEX_ENTRY_SIZE)
        #     data = self.fs.read(self.INDEX_ENTRY_SIZE)
        #     if data.strip(b"\0") == b"":
        #         break

        #     file_index = FileIndexNode.from_bytes(data, self)
        #     files.append(file_index)

        # return files

    def list_directory_contents(self, dir_name: str) -> List[str]:
        dir_node = self.get_file_by_name(dir_name)
        if not dir_node or not dir_node.is_directory:
            raise Exception("Directory does not exist or is not a directory.")

        dir_node.load_children(self.fs, self, self.index)
        return [child.file_name for child in dir_node.children]

    @reset_seek_to_zero
    def read_file(self, file_index: FileIndexNode) -> bytes:
        self.fs.seek(
            self.BITMAP_SIZE
            + self.FILE_INDEX_SIZE
            + file_index.file_start_block * self.BLOCK_SIZE
        )
        data = []

        for i in range(file_index.file_blocks):
            data.append(self.fs.read(self.BLOCK_SIZE))
            self.fs.seek(
                self.BITMAP_SIZE
                + self.FILE_INDEX_SIZE
                + file_index.file_start_block * self.BLOCK_SIZE
                + i * self.BLOCK_SIZE
            )

        return b"".join(data).rstrip(b"\x00")

    def get_file_by_name(self, file_name: str) -> Optional[FileIndexNode]:
        for file_index in self.index.values():
            if file_index.file_name == file_name:
                return file_index

        return None

        # for i in range(self.MAX_INDEX_ENTRIES):
        #     self.fs.seek(self.BITMAP_SIZE + i * self.INDEX_ENTRY_SIZE)
        #     data = self.fs.read(self.INDEX_ENTRY_SIZE)
        #     if data.strip(b"\0") == b"":
        #         continue

        #     file_index = FileIndexNode.from_bytes(data, self)
        #     if file_index.file_name == file_name:
        #         return file_index
        # return None