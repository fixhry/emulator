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
        d = bytearray(f.read())
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
    header = d[:16]
    prg_size = 16 * 1024
    prg_rom = d[16:prg_size+16]
    chr_rom = d[16+prg_size:]

    return prg_rom, chr_rom


class Memory:
    """
    内存布局 $0000 - $FFFF
    $8000 - $FFFF PRG-ROM

    """
    def __init__(self):
        file = 'nestest.nes'
        prg_rom, chr_rom = load_nes(file)
        self._data = [0] * 32 * 1024
        self._data += prg_rom + prg_rom
        # FIXME
        self.d = self._data

    def _read(self, address):
        if address >= 0x800:
            pass

    def read_byte(self, address):
        return self._data[address]

    def read_word(self, address):
        # 小端
        low = self._data[address]
        high = self._data[address + 1]
        v = (high << 8) + low
        return v

    def write_byte(self, address, value):
        self._data[address] = value

    def write_word(self, address, value):
        low = value & 0xFF
        high = (value >> 8) & 0xFF

        self.write_byte(address, low)
        self.write_byte(address+1, high)
