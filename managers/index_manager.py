import time
from managers.config_manager import ConfigManager
from structs.file_index_node import FileIndexNode


class IndexManager:
    def __init__(self, fs, config_manager: "ConfigManager"):

        self.fs = fs
        self.config_manager = config_manager

        # Cache for index entries
        self.index = {}
        self.index_locations = {}
        self.load_index()

    def load_index(self):
        for i in range(self.config_manager.max_index_entries):
            self.fs.seek(
                self.config_manager.bitmap_size
                + i * self.config_manager.index_entry_size
            )
            data = self.fs.read(self.config_manager.index_entry_size)
            if data.strip(b"\0") == b"":
                continue

            file_index = FileIndexNode.from_bytes(data, self)
            self.index[file_index.id] = file_index
            self.index_locations[file_index.id] = i

    def write_to_index(self, file_index: FileIndexNode) -> None:
        if len(file_index.file_name) > self.config_manager.file_name_size:
            raise ValueError("File name too long.")

        file_index.modification_date = int(round(time.time()))
        if file_index.id in self.index:
            self.index[file_index.id] = file_index
            self.index_locations[file_index.id] = file_index.file_start_block
            self.fs.seek(
                self.config_manager.bitmap_size
                + self.index_locations[file_index.id]
                * self.config_manager.index_entry_size
            )

            self.fs.write(
                file_index.to_bytes(
                    self.config_manager.file_name_size,
                    self.config_manager.max_file_blocks,
                    self.config_manager.file_start_block_index_size,
                    self.config_manager.max_length_childrens,
                )
            )
            return

        self.index[file_index.id] = file_index

        for i in range(self.config_manager.max_index_entries):
            self.fs.seek(
                self.config_manager.bitmap_size
                + i * self.config_manager.index_entry_size
            )
            data = self.fs.read(self.config_manager.index_entry_size)
            if data.strip(b"\0") != b"":
                continue

            # Update the file index
            self.fs.seek(
                self.config_manager.bitmap_size
                + i * self.config_manager.index_entry_size
            )
            self.fs.write(
                file_index.to_bytes(
                    self.config_manager.file_name_size,
                    self.config_manager.max_file_blocks,
                    self.config_manager.file_start_block_index_size,
                    self.config_manager.max_length_childrens,
                )
            )
            # self.index[file_index.id] = file_index
            self.index_locations[file_index.id] = i
            self.fs.flush()
            return

        raise Exception("No space in file index.")

    def find_file_by_id(self, file_id: int) -> FileIndexNode:
        return self.index.get(file_id)

    def find_file_by_name(self, file_name: str) -> FileIndexNode:
        for file_index in self.index.values():
            if file_index.file_name == file_name:
                return file_index
        return None

    def list_all_files(self):
        return list(self.index.values())

    def delete_from_index(self, file_index: FileIndexNode) -> None:
        if file_index.id not in self.index:
            return

        del self.index[file_index.id]

        self.fs.seek(
            self.config_manager.bitmap_size
            + self.index_locations[file_index.id] * self.config_manager.index_entry_size
        )
        self.fs.write(b"\0" * self.config_manager.index_entry_size)
        self.fs.flush()
