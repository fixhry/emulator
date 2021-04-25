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
        self._pattern_tables = [*chr_data]  # 8KB
        self._name_tables = [0] * 0x1000    # 4KB
        self._palettes = [
            (84, 84, 84),
            (0, 30, 116),
            (8, 16, 144),
            (48, 0, 136),
            (68, 0, 100),
            (92, 0, 48),
            (84, 4, 0),
            (60, 24, 0),
            (32, 42, 0),
            (8, 58, 0),
            (0, 64, 0),
            (0, 60, 0),
            (0, 50, 60),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (152, 150, 152),
            (8, 76, 196),
            (48, 50, 236),
            (92, 30, 228),
            (136, 20, 176),
            (160, 20, 100),
            (152, 34, 32),
            (120, 60, 0),
            (84, 90, 0),
            (40, 114, 0),
            (8, 124, 0),
            (0, 118, 40),
            (0, 102, 120),
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
            (236, 238, 236),
            (76, 154, 236),
            (120, 124, 236),
            (176, 98, 236),
            (228, 84, 236),
            (236, 88, 180),
            (236, 106, 100),
            (212, 136, 32),
            (160, 170, 0),
            (116, 196, 0),
            (76, 208, 32),
            (56, 204, 108),
            (56, 180, 204),
            (60, 60, 60),
            (0, 0, 0),
            (0, 0, 0),
            (236, 238, 236),
            (168, 204, 236),
            (188, 188, 236),
            (212, 178, 236),
            (236, 174, 236),
            (236, 174, 212),
            (236, 180, 176),
            (228, 196, 144),
            (204, 210, 120),
            (180, 222, 120),
            (168, 226, 144),
            (152, 226, 180),
            (160, 214, 228),
            (160, 162, 160),
            (0, 0, 0),
            (0, 0, 0),
        ]

    @property
    def pattern_tables(self):
        return self._pattern_tables

    @property
    def palettes(self):
        return self._palettes

    def _read(self, address):
        address &= 0x3FFF                        # 映射 0x4000 - 0xFFFF 到 0x0000 - 0x3FFF
        if 0x3F00 <= address:
            a = (address & 0x3F1F) - 0x3F00      # 映射 0x3F20 - 0x4000 到 0x3F00 - 0x3F1F
            return self._palettes[a]
        elif 0x2000 <= address:
            if 0x3000 <= address:
                a = (address - 0x1000) - 0x2000  # 映射 0x3000 - 0x3F00 到 0x2000 - 0x2EFF
            else:
                a = (address - 0x2000)
            return self._name_tables[a]
        else:
            return self._pattern_tables[address]

    def _write(self, address, data):
        address &= 0x3FFF                        # 映射 0x4000 - 0xFFFF 到 0x0000 - 0x3FFF
        if 0x3F00 <= address:
            a = (address & 0x3F1F) - 0x3F00      # 映射 0x3F20 - 0x4000 到 0x3F00 - 0x3F1F
            self._palettes[a] = data
        elif 0x2000 <= address:
            if 0x3000 <= address:
                a = (address - 0x1000) - 0x2000  # 映射 0x3000 - 0x3F00 到 0x2000 - 0x2EFF
            else:
                a = (address - 0x2000)
            self._name_tables[a] = data
        else:
            self._pattern_tables[address] = data

