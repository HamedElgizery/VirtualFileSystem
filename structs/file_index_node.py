from typing import BinaryIO, Callable, Dict, List, Optional
from utility import reset_seek_to_zero
from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
    from core.file_system import FileSystem

# TODO: need to update code here a bit so it doesnt take the entire filesystem directly if it wants to do an operation or if it will just dont name it config and pass only methods it might need


class FileIndexNode:

    def __init__(
        self,
        file_name: str,
        file_start_block: int,
        file_blocks: int,
        id: int,
        is_directory: Optional[bool] = False,
        children_count: Optional[int] = 0,
        creation_date: Optional[int] = None,
        modification_date: Optional[int] = None,
    ) -> None:
        self.id = id
        self.file_name: str = file_name
        self.file_start_block: int = file_start_block
        self.file_blocks: int = file_blocks
        self.file_size: int = 0  # To be calculated dynamically
        self.is_directory = is_directory

        self.set_dates(creation_date, modification_date)
        self.children_count = children_count

    def set_dates(
        self,
        creation_date: Optional[int] = None,
        modification_date: Optional[int] = None,
    ):
        if creation_date == None:
            self.creation_date = int(round(time.time()))
        else:
            self.creation_date = creation_date

        if modification_date == None:
            self.modification_date = int(round(time.time()))
        else:
            self.modification_date = modification_date

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
        return self.file_blocks * block_size

    def to_bytes(
        self,
        FILE_NAME_SIZE,
        MAX_FILE_BLOCKS,
        FILE_START_BLOCK_INDEX_SIZE,
        MAX_LENGTH_CHILDRENS,
    ) -> bytes:
        id_bytes = self.id.to_bytes(4, byteorder="big")
        file_name_bytes = self.file_name.encode("utf-8").ljust(FILE_NAME_SIZE, b"\0")
        file_blocks_bytes = self.file_blocks.to_bytes(MAX_FILE_BLOCKS, byteorder="big")
        file_start_block_bytes = self.file_start_block.to_bytes(
            FILE_START_BLOCK_INDEX_SIZE, byteorder="big"
        )
        is_directory_byte = b"\1" if self.is_directory else b"\0"
        children_count_bytes = self.children_count.to_bytes(
            MAX_LENGTH_CHILDRENS, byteorder="big"
        )

        creation_date = self.creation_date.to_bytes(4, byteorder="big")
        modifaction_date = self.creation_date.to_bytes(4, byteorder="big")

        return (
            id_bytes
            + file_name_bytes
            + file_blocks_bytes
            + file_start_block_bytes
            + is_directory_byte
            + children_count_bytes
            + creation_date
            + modifaction_date
        )

    @classmethod
    def from_bytes(cls, data: bytes, file_system: "FileSystem") -> "FileIndexNode":
        offset_pointer = 0

        id_bytes = data[offset_pointer : offset_pointer + 4]
        offset_pointer += 4

        file_name_bytes = data[
            offset_pointer : offset_pointer + file_system.config_manager.file_name_size
        ]
        offset_pointer += file_system.config_manager.file_name_size

        file_blocks_bytes = data[
            offset_pointer : offset_pointer + file_system.config_manager.max_file_blocks
        ]
        offset_pointer += file_system.config_manager.max_file_blocks

        file_start_block_bytes = data[
            offset_pointer : offset_pointer
            + file_system.config_manager.file_start_block_index_size
        ]
        offset_pointer += file_system.config_manager.file_start_block_index_size

        is_directory_byte = data[offset_pointer : offset_pointer + 1]
        offset_pointer += 1

        children_count_bytes = data[
            offset_pointer : offset_pointer
            + file_system.config_manager.max_length_childrens
        ]
        offset_pointer += file_system.config_manager.max_length_childrens

        creation_date_bytes = data[offset_pointer : offset_pointer + 4]
        offset_pointer += 4

        modification_date_bytes = data[offset_pointer : offset_pointer + 4]
        offset_pointer += 4

        id = int.from_bytes(id_bytes, byteorder="big")
        file_name = file_name_bytes.rstrip(b"\x00").decode("utf-8")
        file_blocks = int.from_bytes(file_blocks_bytes, byteorder="big")
        file_start_block = int.from_bytes(file_start_block_bytes, byteorder="big")
        is_directory = is_directory_byte == b"\1"
        children_count = int.from_bytes(children_count_bytes, byteorder="big")
        creation_date = int.from_bytes(creation_date_bytes, byteorder="big")
        modification_date = int.from_bytes(modification_date_bytes, byteorder="big")

        instance = cls(
            file_name,
            file_start_block,
            file_blocks,
            id,
            is_directory,
            children_count,
            creation_date,
            modification_date,
        )
        instance.calculate_file_size(file_system.config_manager.block_size)
        return instance

    def load_children(self, file_system: "FileSystem") -> List["FileIndexNode"]:

        if not self.is_directory:
            return
        children = []
        children_data_start = (
            file_system.config_manager.bitmap_size
            + file_system.config_manager.file_index_size
            + self.file_start_block * file_system.config_manager.block_size
        )
        file_system.fs.seek(children_data_start)
        for _ in range(self.children_count):
            child_indentifier = file_system.fs.read(4)
            child_node = file_system.index_manager.index[
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
            file_system.config_manager.bitmap_size
            + file_system.config_manager.file_index_size
            + self.file_start_block * file_system.config_manager.block_size
            + 4 * self.children_count
        )

        if (
            4 * (self.children_count + 1)
            >= self.file_blocks * file_system.config_manager.block_size
        ):
            file_system.realign(self)

        children_data_start = (
            file_system.config_manager.bitmap_size
            + file_system.config_manager.file_index_size
            + self.file_start_block * file_system.config_manager.block_size
            + 4 * self.children_count
        )

        file_system.fs.seek(children_data_start)
        file_system.fs.write(child_to_write.id.to_bytes(4, byteorder="big"))
        file_system.fs.flush()
        self.children_count += 1

    def remove_child(self, file_system: "FileSystem", child_dir: str) -> None:

        children = self.load_children(file_system)
        found = False

        for i, child in enumerate(children):
            if file_system.index_manager.index[child.id].file_name == child_dir:
                found = True
                continue

            if found:
                child_data_start = (
                    file_system.config_manager.bitmap_size
                    + file_system.config_manager.file_index_size
                    + self.file_start_block * file_system.config_manager.block_size
                    + 4 * (i - 1)
                )

                if (
                    4 * (i - 1)
                    >= self.file_blocks * file_system.config_manager.block_size
                ):
                    raise ValueError(
                        f"Directory {child_dir} is not a child of {self.file_name}"
                    )

                file_system.fs.seek(child_data_start)
                file_system.fs.write(child.id.to_bytes(4, byteorder="big"))

        if not found:
            raise ValueError(f"Child '{child_dir}' not found.")

        file_system.fs.flush()
        self.children_count -= 1

    # def remove_all_children(self, file_system: "FileSystem") -> None:
    #     file_system.bitmap_manager.free_blocks(
    #         range(
    #             self.file_start_block + 1, self.file_start_block + 1 + self.file_blocks
    #         )
    #     )
    #     self.children_count = 0
    #     self.file_blocks = 1
