import math

from structs.metadata import Metadata


class ConfigManager:
    def __init__(self, metadata: "Metadata"):
        """
        Initialize the configuration manager with dynamic settings derived from metadata.

        :param metadata: A Metadata object containing basic settings.
        """
        # Basic settings from metadata
        self.file_system_path = metadata.file_system_path
        self.file_index_size = metadata.file_index_size
        self.block_size = metadata.block_size
        self.file_system_size = metadata.file_system_size
        self.file_name_size = metadata.file_name_size

        # Dynamically calculated settings
        self.num_blocks = self.file_system_size // self.block_size
        self.max_file_blocks = self._calculate_max_file_blocks()
        self.file_start_block_index_size = self.max_file_blocks
        self.max_length_children = self.file_start_block_index_size
        self.index_entry_size = self._calculate_index_entry_size()
        self.max_index_entries = self.file_index_size // self.index_entry_size
        self.bitmap_size = self.num_blocks // 8

    def _calculate_max_file_blocks(self):
        return math.ceil(math.log2(self.num_blocks) / 8)

    def _calculate_index_entry_size(self):
        return (
            4  # File ID
            + self.file_name_size  # File name
            + self.max_file_blocks  # File blocks
            + self.file_start_block_index_size  # Start block index size
            + 1  # Is directory flag
            + self.max_length_children  # Max children size
            # + self.file_start_block_index_size  # Start block index for children
            + 4  # Creation date
            + 4  # Modification date
        )

    def __repr__(self):
        return (
            f"ConfigManager(\n"
            f"  file_system_path={self.file_system_path},\n"
            f"  file_index_size={self.file_index_size},\n"
            f"  block_size={self.block_size},\n"
            f"  file_system_size={self.file_system_size},\n"
            f"  file_name_size={self.file_name_size},\n"
            f"  num_blocks={self.num_blocks},\n"
            f"  max_file_blocks={self.max_file_blocks},\n"
            f"  file_start_block_index_size={self.file_start_block_index_size},\n"
            f"  max_length_children={self.max_length_children},\n"
            f"  index_entry_size={self.index_entry_size},\n"
            f"  max_index_entries={self.max_index_entries},\n"
            f"  bitmap_size={self.bitmap_size}\n"
            f")"
        )
