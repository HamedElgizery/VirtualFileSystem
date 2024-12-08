import os
from dataclasses import dataclass


@dataclass
class Metadata:
    file_system_path: str
    file_index_size: int
    block_size: int
    file_system_size: int
    file_name_size: int
    current_id: int = 1


class MetadataManager:
    def __init__(self, file_path, metadata: Metadata = None):
        self.file_path = file_path
        if metadata:
            self.metadata = metadata
            self.write_metadata_file()
        else:
            self.metadata = self.read_metadata_file()

    def read_metadata_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Metadata file '{self.file_path}' not found.")

        with open(f"{self.file_path}.dt", "r") as f:
            data = f.read()
        values = data.split(",")

        metadata = Metadata(
            values[0],
            int(values[1]),
            int(values[2]),
            int(values[3]),
            int(values[4]),
            int(values[5]),
        )
        return metadata

    def write_metadata_file(self):
        metadata_values = [
            self.metadata.file_system_path,
            self.metadata.file_index_size,
            self.metadata.block_size,
            self.metadata.file_system_size,
            self.metadata.file_name_size,
            self.metadata.current_id,
        ]
        with open(f"{self.file_path}.dt", "w") as f:
            f.write(",".join(map(str, metadata_values)))

    def increment_id(self):
        self.metadata.current_id += 1
        self.write_metadata_file()
        return self.metadata.current_id

    @property
    def current_id(self):
        return self.metadata.current_id

    @current_id.setter
    def current_id(self, value):
        self.metadata.current_id = value
        self.write_metadata_file()


# class MetadataManager:
#     def __init__(self, file_path):
#         self.file_path = file_path
#         self.f = open(f"{self.file_path}.dt", "r+")
#         self.f.seek(-1, os.SEEK_END)
#         self.current_id = int(self.f.read(1))

#     def __del__(self):
#         self.f.close()

#     def update_id(self):
#         self.current_id += 1
#         self.f.seek(-1, os.SEEK_END)
#         self.f.write(str(self.current_id))
#         self.f.flush()

#     @property
#     def current_id(self):
#         return self._current_id

#     @current_id.setter
#     def current_id(self, value):
#         self._current_id = value
