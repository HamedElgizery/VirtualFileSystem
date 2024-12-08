import os
from dataclasses import dataclass


@dataclass
class Metadata:
    file_system_path: str
    file_index_size: int
    block_size: int
    file_system_size: int
    file_name_size: int


def write_metadata_file(file_path, metadata_values: Metadata):
    metadata_values = [
        metadata_values.file_system_path,
        metadata_values.file_index_size,
        metadata_values.block_size,
        metadata_values.file_system_size,
        metadata_values.file_name_size,
    ]
    with open(f"{file_path}.dt", "w") as f:
        f.write(",".join(map(str, metadata_values)))


def read_metadata_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metadata file '{file_path}' not found.")

    with open(f"{file_path}.dt", "r") as f:
        data = f.read()
    values = data.split(",")

    metadata = Metadata(
        values[0], int(values[1]), int(values[2]), int(values[3]), int(values[4])
    )
    return metadata
