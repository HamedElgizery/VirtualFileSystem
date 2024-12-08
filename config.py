import math

# File System Config
FILE_SYSTEM_PATH = "file"
FILE_INDEX_SIZE = 4096
BLOCK_SIZE = 32
FILE_SYSTEM_SIZE = 1024 * 1024 * 1
NUM_BLOCKS = FILE_SYSTEM_SIZE // BLOCK_SIZE


# File Config
MAX_LENGTH_CHILDRENS = 4
FILE_NAME_SIZE = 32
MAX_FILE_BLOCKS = math.ceil(math.log2(NUM_BLOCKS) / 8)
CHILD_POINTER_SIZE = MAX_FILE_BLOCKS
# FILE_START_BLOCK_INDEX_SIZE = math.ceil(math.log2(FILE_SYSTEM_SIZE) / 8)
FILE_START_BLOCK_INDEX_SIZE = MAX_FILE_BLOCKS

# TODO: okay here basically we need a way to make all teh functions that read and write to index dynamic when it comes to if directory flag is true or just have a delimiter byte
INDEX_ENTRY_SIZE = (
    FILE_NAME_SIZE
    + MAX_FILE_BLOCKS
    + FILE_START_BLOCK_INDEX_SIZE
    + 1
    + MAX_LENGTH_CHILDRENS
    + CHILD_POINTER_SIZE
)
MAX_INDEX_ENTRIES = FILE_INDEX_SIZE // INDEX_ENTRY_SIZE
BITMAP_SIZE = NUM_BLOCKS // 8
INDEX_PAGE_SIZE = min(1048 * 1048, 128 * INDEX_ENTRY_SIZE) // INDEX_ENTRY_SIZE