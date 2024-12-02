import math

# File System Config
FILE_SYSTEM_PATH = "file"
FILE_INDEX_SIZE = 1024
BLOCK_SIZE = 512
FILE_SYSTEM_SIZE = 1024 * 1024 * 1
NUM_BLOCKS = FILE_SYSTEM_SIZE // BLOCK_SIZE

# File Config
FILE_NAME_SIZE = 32
MAX_FILE_SIZE = 32
FILE_START_ADDRESS_SIZE = math.ceil(math.log2(FILE_SYSTEM_SIZE) / 8)
INDEX_ENTRY_SIZE = FILE_NAME_SIZE + MAX_FILE_SIZE + FILE_START_ADDRESS_SIZE
MAX_INDEX_ENTRIES = FILE_INDEX_SIZE // INDEX_ENTRY_SIZE
BITMAP_SIZE = NUM_BLOCKS // 8
