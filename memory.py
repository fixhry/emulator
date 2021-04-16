from utils import log


def load_nes(file):
    """
    nes 文件格式
    16 字节文件头
    16k 字节的程序
    8k 字节的图块数据

    :param file: nes file
    :return:
    """
    with open(file, 'rb') as f:
        d = list(f.read())
    # # 16 bytes header
    # # NES$1A
    # d.pop(0)
    # d.pop(0)
    # d.pop(0)
    # d.pop(0)
    # # PRG-ROM size
    # prg_size_lsb = d.pop(0)
    # # CHR-ROM size
    # chr_size_lsb = d.pop(0)
    # # ROM Control Byte 1
    # d.pop(0)
    # # ROM Control Byte 2
    # d.pop(0)
    # #
    # d.pop(0)
    # #
    h6 = d[6]
    has_trainer = (h6 >> 1) & 1
    # log('has_trainer', has_trainer)
    prg_size = 16 * 1024
    prg_rom = d[16:prg_size+16]
    # d1 = d[16:25]
    # d1 = prg_rom[0x3FFA:]
    # log('prg_head', [hex(i) for i in d1])
    chr_rom = d[16+prg_size:]

    return prg_rom, chr_rom


class Memory:
    def __init__(self, size=0x10000):
        self._data = [0] * size

    @property
    def size(self):
        s = hex(len(self._data))
        return s

    def _read(self, address):
        return self._data[address]

    def _write(self, address, value):
        self._data[address] = value

    def read_byte(self, address):
        return self._read(address)

    def read_word(self, address):
        # 小端
        low = self._read(address)
        high = self._read(address+1)
        v = (high << 8) + low
        return v

    def write_byte(self, address, value):
        self._write(address, value)

    def write_word(self, address, value):
        low = value & 0xFF
        high = (value >> 8) & 0xFF

        self.write_byte(address, low)
        self.write_byte(address+1, high)


class RAM(Memory):
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
    def __init__(self):
        super().__init__()
        self._setup_memory()
        self.d = self._data

    def _setup_memory(self):
        file = 'nestest.nes'
        prg_rom, chr_rom = load_nes(file)
        self._data = [0] * 32 * 1024
        # map PRG-ROM
        self._data += prg_rom + prg_rom
        # self._data[0x2000] = 0x00A0

    # def _read(self, address):
    #     if 0x8000 <= address <= 0xFFFF:
    #         a = address & 0x3FFF
    #         return self._data[a]
    #     else:
    #         return self._data[address]

    def _write(self, address, value):
        a, v = address, value
        if (a > 0x0000) and (a < 0x0800):
            """
            Memory locations $0000-$07FF are mirrored three times at $0800-$1FFF.
            This means that, for example, any data written to $0000 will also be
            written to $0800, $1000 and $1800.
            """
            self._data[a] = value
            a1 = a + 0x0800
            a2 = a + 0x1000
            a3 = a + 0x1800
            self._data[a1] = value
            self._data[a2] = value
            self._data[a3] = value
        else:
            self._data[address] = value


class VRAM(Memory):
    """
    PPU can also address 64 KB of memory although it only has 16 KB of physical RAM
    any address above $3FFF is wrapped around, making the logical
    memory locations $4000-$FFFF effectively a mirror of locations $0000-$3FFF

    $0000-$1000
        pattern table 0
    $1000-$2000
        pattern table 1

    """
    def __init__(self, cartridge):
        super().__init__()
        self._cartridge = cartridge
        self._data = []
        self._setup_vram()

    @property
    def pattern_tables(self):
        return self._data[:0x2000]

    def _setup_vram(self):
        self._setup_pattern_tables()
        self._data += ([0] * 0x2000)

    def _setup_pattern_tables(self):
        self._data += self._cartridge.chr_rom


