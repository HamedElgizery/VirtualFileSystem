from typing import BinaryIO, Callable, Dict, List
from utility import reset_seek_to_zero
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file_system import FileSystem

# TODO: need to update code here a bit so it doesnt take the entire filesystem directly if it wants to do an operation or if it will just dont name it config and pass only methods it might need


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
    def from_bytes(cls, data: bytes, file_system: "FileSystem") -> "FileIndexNode":
        offset_pointer = 0

        id_bytes = data[offset_pointer : offset_pointer + 4]
        offset_pointer += 4

        file_name_bytes = data[
            offset_pointer : offset_pointer + file_system.FILE_NAME_SIZE
        ]
        offset_pointer += file_system.FILE_NAME_SIZE

        file_blocks_bytes = data[
            offset_pointer : offset_pointer + file_system.MAX_FILE_BLOCKS
        ]
        offset_pointer += file_system.MAX_FILE_BLOCKS

        file_start_block_bytes = data[
            offset_pointer : offset_pointer + file_system.FILE_START_BLOCK_INDEX_SIZE
        ]
        offset_pointer += file_system.FILE_START_BLOCK_INDEX_SIZE

        is_directory_byte = data[offset_pointer : offset_pointer + 1]
        offset_pointer += 1

        children_count_bytes = data[
            offset_pointer : offset_pointer + file_system.MAX_LENGTH_CHILDRENS
        ]
        offset_pointer += file_system.MAX_LENGTH_CHILDRENS

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
        instance.calculate_file_size(file_system.BLOCK_SIZE)
        return instance

    def load_children(self, file_system: "FileSystem") -> List["FileIndexNode"]:

        if not self.is_directory:
            return
        children = []
        children_data_start = (
            file_system.BITMAP_SIZE
            + file_system.FILE_INDEX_SIZE
            + self.file_start_block * file_system.BLOCK_SIZE
        )
        file_system.fs.seek(children_data_start)
        for _ in range(self.children_count):
            child_indentifier = file_system.fs.read(4)
            child_node = file_system.index[
                int.from_bytes(child_indentifier, byteorder="big")
            ]
            children.append(child_node)

        return children

    def add_child(
        self, file_system: "FileSystem", child_to_write: "FileIndexNode"
    ) -> None:
        if not self.is_directory:
            return

        children_data_start = (
            file_system.BITMAP_SIZE
            + file_system.FILE_INDEX_SIZE
            + self.file_start_block * file_system.BLOCK_SIZE
            + 4 * self.children_count
        )

        if 4 * (self.children_count + 1) >= self.file_blocks * file_system.BLOCK_SIZE:
            file_system.realign(self)

        children_data_start = (
            file_system.BITMAP_SIZE
            + file_system.FILE_INDEX_SIZE
            + self.file_start_block * file_system.BLOCK_SIZE
            + 4 * self.children_count
        )

        file_system.fs.seek(children_data_start)
        file_system.fs.write(child_to_write.id.to_bytes(4, byteorder="big"))
        self.children_count += 1

    def remove_child(self, file_system: "FileSystem", child_dir: str) -> None:

        children = self.load_children(file_system)
        shifting = False
        for i, child in enumerate(children):
            if file_system.index[child.id].file_name == child_dir:
                shifting = True
                continue

            child_data_start = (
                file_system.BITMAP_SIZE
                + file_system.FILE_INDEX_SIZE
                + self.file_start_block * file_system.BLOCK_SIZE
                + 4 * (i - (1 if shifting else 0))
            )

            file_system.fs.seek(child_data_start)
            file_system.fs.write(child.id.to_bytes(4, byteorder="big"))

        self.children_count -= 1
