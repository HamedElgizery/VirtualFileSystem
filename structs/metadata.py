from dataclasses import dataclass


@dataclass
class Metadata:
    file_system_path: str
    file_index_size: int
    block_size: int
    file_system_size: int
    file_name_size: int
    current_id: int = 1
