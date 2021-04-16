from utils import *


class Cartridge:
    """
    """
    def __init__(self):
        self._setup_cartridge()

    def _setup_cartridge(self):
        self._data_from_nes_file()

    def _data_from_nes_file(self):
        file = 'nestest.nes'
        with open(file, 'rb') as f:
            d = list(f.read())
        header = d[:16]
        mapper_low = (d[6] >> 4) & 0b1111
        mapper_high = (d[7] >> 4) & 0b1111
        mapper = (mapper_high << 4) + mapper_low
        # log('mapper', mapper)
        # 低 8 位
        prg_size_lsb = d[4]
        chr_size_lsb = d[5]
        h9 = d[9]
        prg_size_msb = (h9 >> 4) & 0b1111
        chr_size_msb = h9 & 0b1111
        prg_rom_size = int((prg_size_lsb * 16 * 1024 + prg_size_msb * 8 * 1024) / 8)
        chr_rom_size = int((chr_size_lsb * 16 * 1024 + chr_size_msb * 8 * 1024) / 8)
        # log('PRG-ROM size', prg_rom_size, prg_rom_size / 1024, 'KB')
        # log('CHR-ROM size', chr_rom_size, chr_rom_size / 1024, 'KB')
        prg_size = 16 * 1024
        self._prg_rom = d[16:prg_size+16]
        self._chr_rom = d[16+prg_size:]

    @property
    def chr_rom(self):
        return self._chr_rom

    @property
    def prg_rom(self):
        return self._prg_rom
