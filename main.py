import struct
import os
import math
from typing import List
from config import *  
from utility import reset_seek_to_zero

# FileIndexNode class
class FileIndexNode:
    def __init__(self, file_name: str, file_start_block: int, file_blocks: int) -> None:
        self.file_name: str = file_name
        self.file_start_block: int = file_start_block
        self.file_blocks: int = file_blocks
        self.file_size: int = file_blocks * BLOCK_SIZE  # Calculate file size in bytes

    def to_bytes(self) -> bytes:
        file_name_bytes = self.file_name.encode("utf-8").ljust(FILE_NAME_SIZE, b"\0")
        file_size_bytes = struct.pack(
            f"{MAX_FILE_BLOCKS}B",
            *self.file_blocks.to_bytes(
                MAX_FILE_BLOCKS, byteorder="big"
            ),  # Convert to bytes
        )

        file_start_address_bytes = struct.pack(
            f"{FILE_START_BLOCK_INDEX_SIZE}B",
            *self.file_start_block.to_bytes(
                FILE_START_BLOCK_INDEX_SIZE, byteorder="big"
            ),  # Convert to bytes
        )

        return file_name_bytes + file_size_bytes + file_start_address_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "FileIndexNode":
        file_name_bytes = data[:FILE_NAME_SIZE]
        file_size_bytes = data[FILE_NAME_SIZE : FILE_NAME_SIZE + MAX_FILE_BLOCKS]
        file_start_address_bytes = data[
            FILE_NAME_SIZE
            + MAX_FILE_BLOCKS : FILE_NAME_SIZE
            + MAX_FILE_BLOCKS
            + FILE_START_BLOCK_INDEX_SIZE
        ]

        file_name = file_name_bytes.lstrip(b"\0").decode("utf-8")
        file_size = int.from_bytes(
            struct.unpack(f"{MAX_FILE_BLOCKS}B", file_size_bytes), byteorder="big"
        )

        file_start_address = int.from_bytes(
            struct.unpack(f"{FILE_START_BLOCK_INDEX_SIZE}B", file_start_address_bytes),
            byteorder="big",
        )

        return cls(file_name, file_start_address, file_size)

# FileSystem class
class FileSystem:
    def __init__(self) -> None:
        if not os.path.exists(FILE_SYSTEM_PATH):
            self.fs = open(FILE_SYSTEM_PATH, "w+b")
        else:
            self.fs = open(FILE_SYSTEM_PATH, "r+b")

        if os.path.getsize(FILE_SYSTEM_PATH) == 0:
            self.reserve_file()

        self.bitmap = self.load_bitmap()

    @reset_seek_to_zero
    def reserve_file(self) -> None:
        self.fs.seek(BITMAP_SIZE + FILE_INDEX_SIZE + FILE_SYSTEM_SIZE - 1)
        self.fs.write(b"\0")

    @reset_seek_to_zero
    def load_bitmap(self) -> bytearray:
        return bytearray(self.fs.read(BITMAP_SIZE))

    def find_free_space_bitmap(self, required_blocks: int):
        free_blocks = []

        for i in range(NUM_BLOCKS):
            byte_index = i // 8
            bit_index = i % 8

            if not self.bitmap[byte_index] & (1 << bit_index):
                free_blocks.append(i)
                if len(free_blocks) == required_blocks:
                    break

        if len(free_blocks) < required_blocks:
            raise Exception("no free space")

        return free_blocks

    def write_file(self, file_name: str, file_data: bytes):
        num_blocks_needed = (len(file_data) + BLOCK_SIZE - 1) // BLOCK_SIZE
        free_blocks = self.find_free_space_bitmap(num_blocks_needed)
        file_start_block_index = free_blocks[0]
        current_offset = 0

        # Check if the file exists
        existing_file = self.get_file_by_name(file_name)

        if existing_file:
            # If the file exists, we will overwrite its blocks
            # Free up the blocks used by the existing file in the bitmap
            for block in range(existing_file.file_start_block, existing_file.file_start_block + existing_file.file_blocks):
                byte_index = block // 8
                bit_index = block % 8
                self.bitmap[byte_index] &= ~(1 << bit_index)
                self.update_bitmap(byte_index)
        else:
            # If the file doesn't exist, we'll allocate new blocks
            current_offset = 0

        # Write the new data to free blocks
        for block in free_blocks:
            self.fs.seek(BITMAP_SIZE + FILE_INDEX_SIZE + block * BLOCK_SIZE)
            block_data = file_data[current_offset : current_offset + BLOCK_SIZE]
            self.fs.write(block_data.ljust(BLOCK_SIZE, b"\0"))
            current_offset += len(block_data)

        # Update bitmap to reflect that these blocks are now used
        for block in free_blocks:
            byte_index = block // 8
            bit_index = block % 8
            self.bitmap[byte_index] |= 1 << bit_index
            self.update_bitmap(byte_index)

        # Update the file index with the new or overwritten file details
        file_index_node = FileIndexNode(
            file_name=file_name,
            file_start_block=file_start_block_index,
            file_blocks=num_blocks_needed,
        )

        self.write_to_index(file_index_node)

    @reset_seek_to_zero
    def update_bitmap(self, byte_index) -> None:
        self.fs.seek(byte_index)
        self.fs.write(bytes([self.bitmap[byte_index]]))

    def write_to_index(self, file_index: FileIndexNode) -> None:
        if len(file_index.file_name) > FILE_NAME_SIZE:
            raise ValueError("file name too long")

        for i in range(MAX_INDEX_ENTRIES):
            self.fs.seek(BITMAP_SIZE + i * INDEX_ENTRY_SIZE)
            data = self.fs.read(INDEX_ENTRY_SIZE)
            if data.strip(b"\0") != b"":
                continue

            # Update the file index
            self.fs.seek(BITMAP_SIZE + i * INDEX_ENTRY_SIZE)
            self.fs.write(file_index.to_bytes())
            return

        raise Exception("no free space")

    @reset_seek_to_zero
    def list_all_files(self) -> List[FileIndexNode]:
        files = []

        for i in range(MAX_INDEX_ENTRIES):
            self.fs.seek(BITMAP_SIZE + i * INDEX_ENTRY_SIZE)
            data = self.fs.read(INDEX_ENTRY_SIZE)
            if data.strip(b"\0") == b"":
                break

            file_index = FileIndexNode.from_bytes(data)
            files.append(file_index)

        return files

    @reset_seek_to_zero
    def read_file(self, file_index: FileIndexNode) -> bytes:
        self.fs.seek(
            BITMAP_SIZE + FILE_INDEX_SIZE + file_index.file_start_block * BLOCK_SIZE
        )
        data = []

        for i in range(file_index.file_blocks):
            data.append(self.fs.read(BLOCK_SIZE))
            self.fs.seek(
                BITMAP_SIZE
                + FILE_INDEX_SIZE
                + file_index.file_start_block * BLOCK_SIZE
                + i * BLOCK_SIZE
            )

        return b"".join(data).rstrip(b"\x00")

    def get_file_by_name(self, file_name: str) -> FileIndexNode:
        """Check if the file exists by its name"""
        for i in range(MAX_INDEX_ENTRIES):
            self.fs.seek(BITMAP_SIZE + i * INDEX_ENTRY_SIZE)
            data = self.fs.read(INDEX_ENTRY_SIZE)
            if data.strip(b"\0") == b"":
                continue

            file_index = FileIndexNode.from_bytes(data)
            if file_index.file_name == file_name:
                return file_index
        return None

if __name__ == "__main__":
    fs = FileSystem()

    # Test: Write and overwrite a file
    file_name = "ahmed_hesham.txt"
    file_data = b"my name is H H"
    fs.write_file(file_name, file_data)  # Write initial file

    # Overwrite with new data
    new_file_data = b"my name is H H with extra content"
    fs.write_file(file_name, new_file_data)  # Overwrite existing file

    # List all files and print storage details
    for file in fs.list_all_files():
        print(f"File Name: {file.file_name}")
        print(f"File Blocks: {file.file_blocks}")
        print(f"File Start Block: {file.file_start_block}")
        print(f"File Size (in bytes): {file.file_size}")
        print(f"File Content: {fs.read_file(file)}")
