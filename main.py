import struct
import os
from config import *
from typing import *
from utility import reset_seek_to_zero


class FileIndex:
    pass


class FileIndexNode:
    def __init__(self, file_name: str, file_start_address: int, file_size: int) -> None:
        self.file_name: str = file_name
        self.file_start_address: int = file_start_address
        self.file_size: int = file_size

    def to_bytes(self) -> bytes:
        file_name_bytes = self.file_name.encode("utf-8").ljust(FILE_NAME_SIZE, b"\0")
        file_size_bytes = struct.pack(
            f"{MAX_FILE_SIZE}s", str(self.file_size).encode("utf-8")
        )
        file_start_address_bytes = struct.pack(
            f"{FILE_START_ADDRESS_SIZE}s", str(self.file_start_address).encode("utf-8")
        )

        return file_name_bytes + file_size_bytes + file_start_address_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "FileIndexNode":
        file_name_bytes = data[:FILE_NAME_SIZE]
        file_size_bytes = data[FILE_NAME_SIZE : FILE_NAME_SIZE + MAX_FILE_SIZE]
        file_start_address_bytes = data[
            FILE_NAME_SIZE
            + MAX_FILE_SIZE : FILE_NAME_SIZE
            + MAX_FILE_SIZE
            + FILE_START_ADDRESS_SIZE
        ]

        file_name = file_name_bytes.lstrip(b"\0").decode("utf-8")
        file_size = int(
            struct.unpack(f"{MAX_FILE_SIZE}s", file_size_bytes)[0]
            .decode("utf-8")
            .rstrip("\0")
        )
        file_start_address = int(
            struct.unpack(f"{FILE_START_ADDRESS_SIZE}s", file_start_address_bytes)[0]
            .decode("utf-8")
            .rstrip("\0")
        )

        return cls(file_name, file_start_address, file_size)


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

        file_start_address = free_blocks[0] * BLOCK_SIZE
        current_offset = 0

        for block in free_blocks:
            self.fs.seek(BITMAP_SIZE + FILE_INDEX_SIZE + block * BLOCK_SIZE)
            block_data = file_data[current_offset : current_offset + BLOCK_SIZE]
            self.fs.write(block_data.ljust(BLOCK_SIZE, b"\0"))
            current_offset += len(block_data)

        for block in free_blocks:
            byte_index = block // 8
            bit_index = block % 8
            self.bitmap[byte_index] |= 1 << bit_index
            self.update_bitmap(byte_index)

        file_index_node = FileIndexNode(
            file_name=file_name,
            file_start_address=file_start_address,
            file_size=len(file_data),
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

            self.fs.seek(BITMAP_SIZE + i * INDEX_ENTRY_SIZE)
            self.fs.write(file_index.to_bytes())

            return

        raise Exception("no free space")

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

    def read_file(self, file_name: str) -> bytes:
        pass


if __name__ == "__main__":
    fs = FileSystem()

    file_name = "ahmed_hesham.txt"
    file_data = b"my name is H"

    # fs.write_file(file_name, file_data)

    for i in fs.list_all_files():
        print(i.file_name, i.file_size, i.file_start_address)
