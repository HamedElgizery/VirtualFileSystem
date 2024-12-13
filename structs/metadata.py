from dataclasses import dataclass


@dataclass
class Metadata:
    file_system_path: str
    file_index_size: int = 1024
    block_size: int = 32
    file_system_size: int = 1024 * 128
    file_name_size: int = 36
    current_id: int = 1
