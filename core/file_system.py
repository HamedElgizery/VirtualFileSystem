import logging
import math
import os
import time
from typing import List, Optional, Tuple, Union
from structs.file_index_node import FileIndexNode
from structs.metadata import Metadata
from utility import open_file_without_cache, reset_seek_to_zero
from managers.index_manager import IndexManager
from managers.bitmap_manager import BitmapManager
from managers.config_manager import ConfigManager
from managers.metadata_manager import MetadataManager
from managers.transaction_manager import TransactionManager

# TODO: ensure no 2 file systems are open for the same file
# TODO: ensure nothing can be done to the root directory


class FileSystem:
    ROOT_DIR = "root"

    def __init__(
        self,
        file_system_name: str,
        user_id: str,
        specs: Optional[Metadata] = None,
    ) -> None:
        self.user_id = user_id
        self.logger = logging.getLogger(self.user_id)

        if specs:
            self.metedata_manager = MetadataManager(file_system_name, specs)
            self.config_manager = ConfigManager(specs)
        else:
            self.metedata_manager = MetadataManager(file_system_name)
            self.config_manager = ConfigManager(self.metedata_manager.metadata)

        self.fs_path_name = f"{self.config_manager.file_system_path}"

        if not os.path.exists(self.fs_path_name):
            self.fs = open_file_without_cache(self.fs_path_name, "w+b")
        else:
            self.fs = open_file_without_cache(self.fs_path_name, "r+b")
        if os.path.getsize(self.fs_path_name) == 0:
            self.reserve_file()

        self.bitmap_manager = BitmapManager(
            self.fs,
            self.config_manager.num_blocks,
            self.config_manager.block_size,
            self.config_manager.bitmap_size,
        )
        self.index_manager = IndexManager(self.fs, self.config_manager)
        self.transaction_manager = TransactionManager()

        FileIndexNode.id_generator = lambda: self.metedata_manager.increment_id()

        root = self.index_manager.find_file_by_name(FileSystem.ROOT_DIR)
        if not root:
            root = FileIndexNode(FileSystem.ROOT_DIR, 0, 1, is_directory=True)
            root.id = 0  # id of the root directory is 0
            root.calculate_file_size(self.config_manager.block_size)

            self.bitmap_manager.mark_used(0)
            self.index_manager.write_to_index(root)

        self.logger.info(f"FileSystem initialized: {self.user_id}")

    def __del__(self):
        self.shut_down()

    def shut_down(self):
        self.logger.info("FileSystem shutting down...")
        self.fs.flush()
        self.fs.close()

    """
    Utility Functions.
    """

    def is_directory(self, file_path: str) -> bool:
        return self.resolve_path(file_path).is_directory

    def exists(self, file_path: str) -> bool:
        try:
            self.resolve_path(file_path)
            return True
        except:
            return False

    def update_file_access_time(self, file_path: str) -> None:
        file_node = self.resolve_path(file_path)
        self.index_manager.write_to_index(file_node)

    def resolve_path(
        self, path: str, return_parent: bool = False
    ) -> Union[FileIndexNode, Tuple[FileIndexNode, FileIndexNode]]:
        """
        Resolves a given path to the corresponding FileIndexNode(s).

        :param path: The path to resolve.
        :param return_parent: If True, return both the parent and the target node.
        :return: The resolved FileIndexNode, or a tuple of (parent_node, target_node) if return_parent is True.
        """
        # Normalize and split the path into components
        directories = [d for d in path.split("/") if d not in ("", ".")]

        # Start from the root or current directory based on the path
        current_id = 0 if path.startswith("/") else self.index_manager.index[0].id
        parent_id = 0 if path.startswith("/") else self.index_manager.index[0].id

        # Handle edge case for root path
        if not directories:  # Path is `/` or equivalent
            root_node = self.index_manager.index[current_id]
            return (root_node, root_node) if return_parent else root_node

        for i, directory in enumerate(directories):
            if directory == "..":
                # Move to the parent directory
                parent_id = current_id
                parent_dir = self.index_manager.index[current_id]
                current_id = parent_dir.id
                continue

            if i == 0 and directory == FileSystem.ROOT_DIR:
                # Skip root directory marker if it's the first component
                continue

            # Check if it's the last component
            is_last_component = i == len(directories) - 1

            # Traverse to the child directory or file
            for child in self.index_manager.index[current_id].load_children(self):
                if child.file_name == directory:
                    # Update parent and current IDs
                    parent_id = current_id
                    current_id = child.id

                    # If it's the last component and not a directory, stop traversal
                    if is_last_component and not child.is_directory:
                        if return_parent:
                            return self.index_manager.index[parent_id], child
                        return child

                    break
            else:
                raise FileNotFoundError(f"File or directory '{directory}' not found.")

        # Handle return_parent for directories
        if return_parent:
            return (
                self.index_manager.index[parent_id],
                self.index_manager.index[current_id],
            )

        return self.index_manager.index[current_id]

    """
    File Operations.
    """

    def create_file(self, file_dir: str, file_data: bytes):
        directories = [d for d in file_dir.split("/") if d not in ("", ".")]
        parent_node = self.resolve_path("/".join(directories[:-1]))
        # parent_node = self.get_file_by_name(parent_dir)
        if not parent_node.is_directory:
            raise Exception("Parent directory does not exist or is not a directory.")

        num_blocks_needed = math.ceil(len(file_data) / self.config_manager.block_size)

        num_blocks_needed = max(num_blocks_needed, 1)
        free_blocks = self.bitmap_manager.find_free_space_bitmap(num_blocks_needed)
        file_start_block_index = free_blocks[0]

        # TODO: later on we will make use of path so for parent_dir it will take a path and we will check files or folders in it to see if name exists or not
        # Check if the file exists
        existing_file = next(
            (
                child
                for child in parent_node.load_children(self)
                if child.file_name == directories[-1]
            ),
            None,
        )

        if existing_file:
            raise Exception("File already exists.")

        # Write the new data to free blocks
        # current_offset = 0
        # for block in free_blocks:
        #     self.fs.seek(
        #         self.config_manager.bitmap_size
        #         + self.config_manager.file_index_size
        #         + block * self.config_manager.block_size
        #     )
        #     block_data = file_data[
        #         current_offset : current_offset + self.config_manager.block_size
        #     ]
        #     self.fs.write(block_data.ljust(self.config_manager.block_size, b"\0"))
        #     current_offset += len(block_data)

        start_position = (
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + file_start_block_index * self.config_manager.block_size
        )
        self.fs.seek(start_position)
        self.fs.write(
            file_data.ljust(num_blocks_needed * self.config_manager.block_size, b"\0")
        )

        self.logger.info(
            f"Wrote {len(file_data)} bytes to start block {file_start_block_index}"
        )

        # Update bitmap to reflect that these blocks are now used
        self.transaction_manager.add_operation(
            self.bitmap_manager.mark_blocks,
            rollback_func=self.bitmap_manager.free_blocks,
            func_args=[free_blocks],
            rollback_args=[free_blocks],
        )

        # Update the file index
        file_index_node = FileIndexNode(
            file_name=directories[-1],
            file_start_block=file_start_block_index,
            file_blocks=num_blocks_needed,
        )

        self.transaction_manager.add_operation(
            self.clear_blocks_data,
            rollback_func=None,
            func_args=[free_blocks],
            rollback_args=[],
        )

        self.transaction_manager.add_operation(
            parent_node.add_child,
            rollback_func=parent_node.remove_child,
            func_args=[self, file_index_node],
            rollback_args=[self, file_index_node.file_name],
        )

        self.transaction_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[file_index_node],
            rollback_args=[file_index_node],
        )

        self.transaction_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[parent_node],
            rollback_args=[parent_node],
        )

        self.transaction_manager.commit()

    # TODO: i need to centralize this shit i dont want some to work like this and some to work like that but oh well
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

    # TODO: add transcation manager here
    def edit_file(self, file_dir: str, new_data: bytes):

        file_node = self.resolve_path(file_dir)

        if not file_node:
            raise FileNotFoundError("File does not exist.")
        if file_node.is_directory:
            raise ValueError("The specified path is a directory.")

        max_data_size = file_node.file_blocks * self.config_manager.block_size
        new_data_blocks = math.ceil(len(new_data) / self.config_manager.block_size)
        factor = math.ceil(new_data_blocks / file_node.file_blocks)
        if factor >= 2:
            self.realign(file_node, factor)

        start_position = (
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + file_node.file_start_block * self.config_manager.block_size
        )
        self.fs.seek(start_position)
        self.fs.write(
            new_data.ljust(new_data_blocks * self.config_manager.block_size, b"\0")
        )

    def delete_file(self, file_dir: str) -> None:
        parent_node, file_node = self.resolve_path(file_dir, True)

        if not file_node:
            raise ValueError("File doesn't exist")
        if file_node.is_directory:
            raise ValueError("Not a file")

        self.transaction_manager.add_operation(
            self.bitmap_manager.free_blocks,
            rollback_func=self.bitmap_manager.mark_used,
            func_args=[range(file_node.file_blocks), file_node.file_start_block],
            rollback_args=[range(file_node.file_blocks), file_node.file_start_block],
        )
        self.transaction_manager.add_operation(
            parent_node.remove_child,
            rollback_func=parent_node.add_child,
            func_args=[self, file_node.file_name],
            rollback_args=[self, file_node],
        )
        self.transaction_manager.add_operation(
            self.index_manager.delete_from_index,
            rollback_func=self.index_manager.write_to_index,
            func_args=[file_node],
            rollback_args=[file_node],
        )

        self.transaction_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[parent_node],
            rollback_args=[parent_node],
        )

        self.transaction_manager.commit()

    """
    Directory Operations
    """

    def create_directory(self, dir_name: str):
        # parent_node = self.get_file_by_name(parent_dir_name)
        directories = [d for d in dir_name.split("/") if d not in ("", ".")]
        parent_node = self.resolve_path("/".join(directories[:-1]) or "/")
        if not parent_node or not parent_node.is_directory:
            raise Exception("Parent directory does not exist or is not a directory.")
        children = parent_node.load_children(self)
        if any(child.file_name == directories[-1] for child in children):
            raise Exception("Directory already exists.")

        free_block = self.bitmap_manager.find_free_space_bitmap(1)[0]

        new_dir_node = FileIndexNode(
            file_name=directories[-1],
            file_start_block=free_block,
            file_blocks=1,
            is_directory=True,
            children_count=0,
        )

        self.transaction_manager.add_operation(
            self.bitmap_manager.mark_used,
            rollback_func=self.bitmap_manager.free_block,
            func_args=[free_block],
            rollback_args=[free_block],
        )

        self.transaction_manager.add_operation(
            self.clear_block_data,
            rollback_func=None,
            func_args=[free_block],
            rollback_args=[],
        )

        self.transaction_manager.add_operation(
            parent_node.add_child,
            rollback_func=parent_node.remove_child,
            func_args=[self, new_dir_node],
            rollback_args=[self, new_dir_node],
        )

        self.transaction_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[new_dir_node],
            rollback_args=[new_dir_node],
        )

        self.transaction_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[parent_node],
            rollback_args=[parent_node],
        )
        self.transaction_manager.commit()

    def list_directory_contents(self, dir_name: str) -> List[str]:
        # dir_node = self.get_file_by_name(dir_name)
        dir_node = self.resolve_path(dir_name)
        if not dir_node or not dir_node.is_directory:
            raise Exception("Directory does not exist or is not a directory.")

        children = dir_node.load_children(self)
        return [child.file_name for child in children]

    def delete_directory(self, dir_path: str) -> None:

        local_transcation_manager = TransactionManager()

        parent_node, dir_node = self.resolve_path(dir_path, True)
        children = dir_node.load_children(self)

        if not dir_node:
            raise ValueError("Directory doesn't exist")
        if not dir_node.is_directory:
            raise ValueError("Not a directory")

        local_transcation_manager.add_operation(
            self.bitmap_manager.free_blocks,
            rollback_func=self.bitmap_manager.mark_blocks,
            func_args=[range(dir_node.file_blocks), dir_node.file_start_block],
            rollback_args=[range(dir_node.file_blocks), dir_node.file_start_block],
        )

        for child in children:
            if child.is_directory:
                local_transcation_manager.add_operation(
                    self.delete_directory,
                    rollback_func=None,
                    func_args=[dir_path + "/" + child.file_name],
                    rollback_args=[],
                )
                continue

            local_transcation_manager.add_operation(
                self.bitmap_manager.free_blocks,
                rollback_func=self.bitmap_manager.mark_blocks,
                func_args=[range(child.file_blocks), child.file_start_block],
                rollback_args=[range(child.file_blocks), child.file_start_block],
            )

            local_transcation_manager.add_operation(
                self.index_manager.delete_from_index,
                rollback_func=self.index_manager.write_to_index,
                func_args=[child],
                rollback_args=[child],
            )

        local_transcation_manager.add_operation(
            parent_node.remove_child,
            rollback_func=parent_node.add_child,
            func_args=[self, dir_node.file_name],
            rollback_args=[self, dir_node],
        )

        local_transcation_manager.add_operation(
            self.index_manager.delete_from_index,
            rollback_func=self.index_manager.write_to_index,
            func_args=[dir_node],
            rollback_args=[dir_node],
        )

        local_transcation_manager.add_operation(
            self.index_manager.write_to_index,
            rollback_func=self.index_manager.delete_from_index,
            func_args=[parent_node],
            rollback_args=[parent_node],
        )

        local_transcation_manager.commit()

    def copy_directory(self, dir_path: str, new_dir_path: str) -> None:
        dir_node = self.resolve_path(dir_path)

        if not dir_node:
            raise ValueError("Directory doesn't exist")

        if not dir_node.is_directory:
            raise ValueError("Not a directory")

        children = dir_node.load_children(self)

        self.create_directory(new_dir_path)
        for child in children:
            self.copy_file(
                f"{dir_path}/{child.file_name}", f"{new_dir_path}/{child.file_name}"
            )

    """
    Other Operations.
    """

    # TODO: add a method which will also automically copy all the older blocks and expand
    def realign(self, file_index: FileIndexNode, factor: int = 2) -> None:
        if file_index.is_directory:
            children = file_index.load_children(self)
            self.bitmap_manager.free_blocks(
                range(file_index.file_blocks), file_index.file_start_block
            )

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
            self.bitmap_manager.free_blocks(
                range(file_index.file_blocks), file_index.file_start_block
            )

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

    def reserve_file(self) -> None:
        self.fs.seek(
            self.config_manager.bitmap_size
            + self.config_manager.file_index_size
            + self.config_manager.file_system_size
            - 1
        )
        self.fs.write(b"\0")

    def list_all_files(self) -> List[FileIndexNode]:
        return list(self.index_manager.index.values())

    def get_file_size(self, file_dir: str) -> int:
        file_node = self.resolve_path(file_dir)
        return file_node.file_blocks * self.config_manager.block_size

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
        parent_node, file_node = self.resolve_path(old_dir, True)
        target_node = self.resolve_path(new_dir)
        if not file_node:
            raise FileNotFoundError(f"File '{old_dir}' not found.")

        if not target_node:
            raise Exception(f"Target directory '{new_dir}' not found.")

        if not target_node.is_directory:
            raise FileNotFoundError(f"{file_node} is not a directory.")

        if file_node.file_name in target_node.load_children(self):
            raise Exception(
                f"File '{file_node.file_name}' already exists in '{new_dir}'."
            )

        self.transaction_manager.add_operation(
            parent_node.remove_child,
            rollback_func=parent_node.add_child,
            func_args=[self, file_node.file_name],
            rollback_args=[self, file_node],
        )

        self.transaction_manager.add_operation(
            target_node.add_child,
            rollback_func=target_node.remove_child,
            func_args=[self, file_node],
            rollback_args=[self, file_node],
        )

        self.transaction_manager.commit()

        # parent_node.remove_child(self, file_node.file_name)
        # target_node.add_child(self, file_node)

        # self.copy_file(old_dir, new_dir)
        # self.delete_file(old_dir)

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

    def clear_block_data(self, block_number: int) -> None:
        self.fs.seek(block_number * self.config_manager.block_size)
        self.fs.write(b"\0" * self.config_manager.block_size)

    def clear_blocks_data(self, blocks: List[int]) -> None:
        for block in blocks:
            self.clear_block_data(block)
