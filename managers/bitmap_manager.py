from typing import BinaryIO, Iterable, List, Optional


class BitmapManager:
    def __init__(self, fs: BinaryIO, num_blocks: int, block_size: int):
        self.fs = fs
        self.bitmap = bytearray(num_blocks // 8)
        self.num_blocks = num_blocks
        self.block_size = block_size

    def load(self):
        self.bitmap = bytearray(self.fs.read(self.BITMAP_SIZE))

    def mark_used(self, block: int):
        byte_index = block // 8
        bit_index = block % 8
        self.bitmap[byte_index] |= 1 << bit_index
        self.fs.seek(byte_index)
        self.fs.write(bytes([self.bitmap[byte_index]]))

    def mark_blocks(self, blocks: Iterable[int], margin: Optional[int] = 0):
        for block in blocks:
            self.mark_used(margin + block)

    def free_block(self, block_number: int) -> None:
        self.bitmap[block_number // 8] &= ~(1 << (block_number % 8))
        self.fs.seek(block_number * self.block_size)
        self.fs.write(b"\0" * self.block_size)

    def free_blocks(self, blocks: Iterable[int], margin: Optional[int] = 0):
        for block in blocks:
            self.free_block(margin + block)

    def find_free_space_bitmap(self, required_blocks):
        free_blocks = []
        start_index = -1
        count = 0

        for i in range(self.num_blocks):
            byte_index = i // 8
            bit_index = i % 8

            if not self.bitmap[byte_index] & (1 << bit_index):
                if count == 0:
                    start_index = i
                count += 1

                if count == required_blocks:
                    free_blocks = list(
                        range(start_index, start_index + required_blocks)
                    )
                    break
            else:
                start_index = -1
                count = 0

        if len(free_blocks) < required_blocks:
            raise Exception("No continuous free space available.")

        return free_blocks
