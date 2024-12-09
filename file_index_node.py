from typing import BinaryIO, Callable, Dict, List
from utility import reset_seek_to_zero


class FileIndexNode:
    id_generator = None

    def __init__(
        self,
        file_name: str,
        file_start_block: int,
        file_blocks: int,
        is_directory: bool = False,
        children_count: int = 0,
        no_id: bool = False,
    ) -> None:
        if not no_id:
            self.id = FileIndexNode.id_generator()
        self.file_name: str = file_name
        self.file_start_block: int = file_start_block
        self.file_blocks: int = file_blocks
        self.file_size: int = 0  # To be calculated dynamically
        self.is_directory = is_directory
        self.children_count = children_count

    def __repr__(self) -> str:
        return (
            f"id={self.id}\n"
            f"file_name={self.file_name!r}\n"
            f"file_start_block={self.file_start_block}\n"
            f"file_blocks={self.file_blocks}\n"
            f"file_size={self.file_size}\n"
            f"is_directory={self.is_directory}\n"
            f"children_count={self.children_count}\n"
            # f"children={self.children!r}\n"
            f"==========================\n"
        )

    def calculate_file_size(self, block_size: int):
        self.file_size = self.file_blocks * block_size

    def to_bytes(
        self,
        FILE_NAME_SIZE,
        MAX_FILE_BLOCKS,
        FILE_START_BLOCK_INDEX_SIZE,
        MAX_LENGTH_CHILDRENS,
    ) -> bytes:
        file_name_bytes = self.file_name.encode("utf-8").ljust(FILE_NAME_SIZE, b"\0")
        file_blocks_bytes = self.file_blocks.to_bytes(MAX_FILE_BLOCKS, byteorder="big")
        file_start_block_bytes = self.file_start_block.to_bytes(
            FILE_START_BLOCK_INDEX_SIZE, byteorder="big"
        )
        is_directory_byte = b"\1" if self.is_directory else b"\0"
        children_count_bytes = self.children_count.to_bytes(
            MAX_LENGTH_CHILDRENS, byteorder="big"
        )

        id_bytes = self.id.to_bytes(4, byteorder="big")

        return (
            id_bytes
            + file_name_bytes
            + file_blocks_bytes
            + file_start_block_bytes
            + is_directory_byte
            + children_count_bytes
        )

    @classmethod
    def from_bytes(cls, data: bytes, config) -> "FileIndexNode":
        offset_pointer = 0

        id_bytes = data[offset_pointer : offset_pointer + 4]
        offset_pointer += 4

        file_name_bytes = data[offset_pointer : offset_pointer + config.FILE_NAME_SIZE]
        offset_pointer += config.FILE_NAME_SIZE

        file_blocks_bytes = data[
            offset_pointer : offset_pointer + config.MAX_FILE_BLOCKS
        ]
        offset_pointer += config.MAX_FILE_BLOCKS

        file_start_block_bytes = data[
            offset_pointer : offset_pointer + config.FILE_START_BLOCK_INDEX_SIZE
        ]
        offset_pointer += config.FILE_START_BLOCK_INDEX_SIZE

        is_directory_byte = data[offset_pointer : offset_pointer + 1]
        offset_pointer += 1

        children_count_bytes = data[
            offset_pointer : offset_pointer + config.MAX_LENGTH_CHILDRENS
        ]
        offset_pointer += config.MAX_LENGTH_CHILDRENS

        id = int.from_bytes(id_bytes, byteorder="big")
        file_name = file_name_bytes.rstrip(b"\x00").decode("utf-8")
        file_blocks = int.from_bytes(file_blocks_bytes, byteorder="big")
        file_start_block = int.from_bytes(file_start_block_bytes, byteorder="big")
        is_directory = is_directory_byte == b"\1"
        children_count = int.from_bytes(children_count_bytes, byteorder="big")

        instance = cls(
            file_name, file_start_block, file_blocks, is_directory, children_count, True
        )
        instance.id = id
        instance.calculate_file_size(config.BLOCK_SIZE)
        return instance

    def load_children(
        self, fs: BinaryIO, config, index: Dict[int, "FileIndexNode"]
    ) -> List[int]:

        if not self.is_directory:
            return
        children = []
        children_data_start = (
            config.BITMAP_SIZE
            + config.FILE_INDEX_SIZE
            + self.file_start_block * config.BLOCK_SIZE
        )
        fs.seek(children_data_start)
        for _ in range(self.children_count):
            child_indentifier = fs.read(4)
            child_node = index[int.from_bytes(child_indentifier, byteorder="big")]
            children.append(child_node)

        return children

    def add_child(self, fs: BinaryIO, child_to_write: "FileIndexNode", config) -> None:
        if not self.is_directory:
            return

        children_data_start = (
            config.BITMAP_SIZE
            + config.FILE_INDEX_SIZE
            + self.file_start_block * config.BLOCK_SIZE
            + 4 * self.children_count
        )

        if 4 * (self.children_count + 1) >= self.file_blocks * config.BLOCK_SIZE:
            children = self.load_children(fs, config, config.index)
            config.free_block(self.file_start_block)

            free_blocks = config.find_free_space_bitmap(self.file_blocks * 2)
            start_block = free_blocks[0]

            self.file_start_block = start_block
            self.file_blocks = len(free_blocks)

            children_data_start = (
                config.BITMAP_SIZE
                + config.FILE_INDEX_SIZE
                + start_block * config.BLOCK_SIZE
            )

            for i, child in enumerate(children):
                fs.seek(children_data_start + i * 4)
                fs.write(child.id.to_bytes(4, byteorder="big"))

            for block in free_blocks:
                byte_index = block // 8
                bit_index = block % 8
                config.bitmap[byte_index] |= 1 << bit_index
                config.update_bitmap(byte_index)

        children_data_start = (
            config.BITMAP_SIZE
            + config.FILE_INDEX_SIZE
            + self.file_start_block * config.BLOCK_SIZE
            + 4 * self.children_count
        )

        fs.seek(children_data_start)
        fs.write(child_to_write.id.to_bytes(4, byteorder="big"))
        self.children_count += 1

    # def save_children(
    #     self,
    #     fs: BinaryIO,
    #     BLOCK_SIZE: int,
    #     config,
    #     free_blocks_func: Callable[[int], List[int]],
    # ) -> None:
    #     if not self.is_directory:
    #         return

    #     free_blocks_required = (len(self.children) * 4) // BLOCK_SIZE
    #     # free_blocks = free_blocks_func(free_blocks_required)
    #     children_data_start = (
    #         config.BITMAP_SIZE
    #         + config.FILE_INDEX_SIZE
    #         + self.file_start_block * config.BLOCK_SIZE
    #     )
    #     fs.seek(children_data_start)
    #     for child in self.children:
    #         fs.write(child.id.to_bytes(4, byteorder="big"))
