from memory.read import MemoryRead
from memory.write import MemoryWrite


class RAM(MemoryRead, MemoryWrite):
    """
    内存布局 $0000 - $FFFF
    $0000 - $2000
        RAM 2KB
    $2000 - $4020
        IO registers
    $4020 - $6000
        expansion ROM
    $6000 - $8000
        SRAM
    $8000 - $FFFF
        PRG-ROM
    """
    def __init__(self, size):
        self._size = size
        self._setup_memory()

    def __getitem__(self, item):
        return self._data[item]

    # TODO __len__
    @property
    def size(self):
        return self._size

    def _setup_memory(self):
        self._data = [0] * self._size

    def _read(self, address):
        return self._data[address]

    def _write(self, address, data):
        self._data[address] = data
