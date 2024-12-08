from typing import BinaryIO, Callable, Dict, List


class FileIndexNode:
    next_id = 1

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
            self.id = FileIndexNode.next_id
            FileIndexNode.next_id += 1
        self.file_name: str = file_name
        self.file_start_block: int = file_start_block
        self.file_blocks: int = file_blocks
        self.file_size: int = 0  # To be calculated dynamically
        self.is_directory = is_directory
        self.children_count = children_count
        self.children = [] if is_directory else None

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
    ) -> None:

        if not self.is_directory:
            return
        self.children = []
        children_data_start = (
            config.BITMAP_SIZE
            + config.FILE_INDEX_SIZE
            + self.file_blocks * config.BLOCK_SIZE
        )
        fs.seek(children_data_start)
        for _ in range(self.children_count):
            child_indentifier = fs.read(4)
            child_node = index[int.from_bytes(child_indentifier, byteorder="big")]
            self.children.append(child_node)

    def save_children(
        self,
        fs: BinaryIO,
        BLOCK_SIZE: int,
        config,
        free_blocks_func: Callable[[int], List[int]],
    ) -> None:
        if not self.is_directory:
            return

        free_blocks_required = (len(self.children) * 4) // BLOCK_SIZE
        # free_blocks = free_blocks_func(free_blocks_required)
        children_data_start = (
            config.BITMAP_SIZE
            + config.FILE_INDEX_SIZE
            + self.file_blocks * config.BLOCK_SIZE
        )
        fs.seek(children_data_start)
        for child in self.children:
            fs.write(child.id.to_bytes(4, byteorder="big"))
            fs.seek(BLOCK_SIZE, 1)
