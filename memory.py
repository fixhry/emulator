class MemoryRead:
    def _read(self, address):
        raise NotImplementedError()

    def read_byte(self, address):
        return self._read(address)

    def read_word(self, address):
        # 小端
        low = self._read(address)
        high = self._read(address+1)
        v = (high << 8) + low
        return v


class MemoryWrite:
    def _write(self, address, data):
        raise NotImplementedError()

    def write_byte(self, address, data):
        return self._write(address, data)

    def write_word(self, address, data):
        low = data & 0xFF
        high = (data >> 8) & 0xFF
        self.write_byte(address, low)
        self.write_byte(address+1, high)


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

    @property
    def size(self):
        return self._size

    def _setup_memory(self):
        self._data = [0] * self._size

    def _read(self, address):
        return self._data[address]

    def _write(self, address, data):
        self._data[address] = data


class VRAM(MemoryRead, MemoryWrite):
    """
    PPU can also address 64 KB of memory although it only has 16 KB of physical RAM
    any address above $3FFF is wrapped around, making the logical
    memory locations $4000-$FFFF effectively a mirror of locations $0000-$3FFF

    $0000-$1000
        pattern table 0
    $1000-$2000
        pattern table 1
    """
    def __init__(self, chr_data):
        self._data = [*chr_data]
        self._setup_vram()

    def _setup_vram(self):
        self._data += ([0] * 0x2000)

    def _read(self, address):
        # TODO Mirror
        return self._data[address]

    def _write(self, address, data):
        self._data[address] = data

