from memory.read import MemoryRead
from memory.write import MemoryWrite
from ppu import MirroringType


class PPUBus(MemoryRead, MemoryWrite):
    def __init__(self, ppu, vram, cartridge, palettes):
        self._vram = vram
        self._cartridge = cartridge
        self._palettes = palettes
        self._ppu = ppu
        self._ppu.connect_to_ppu_bus(self)

    def _write(self, address, data):
        address &= 0x3FFF                           # 映射 0x4000 - 0xFFFF 到 0x0000 - 0x3FFF
        if 0x3F00 <= address:
            a = (address & 0x3F1F) - 0x3F00         # 映射 0x3F20 - 0x4000 到 0x3F00 - 0x3F1F
            self._palettes[a] = data
        elif 0x2000 <= address:
            # name tables
            if 0x3000 <= address:
                a = (address - 0x1000) - 0x2000     # 映射 0x3000 - 0x3F00 到 0x2000 - 0x2EFF
            else:
                a = (address - 0x2000)
            self._vram.write_byte(a, data)
        else:
            raise RuntimeError('ppu write address {} data {}'.format(hex(address), hex(data)))

    def _read(self, address):
        address &= 0x3FFF                               # 映射 0x4000 - 0xFFFF 到 0x0000 - 0x3FFF
        if 0x3F00 <= address:
            a = (address & 0x3F1F) - 0x3F00             # 映射 0x3F20 - 0x4000 到 0x3F00 - 0x3F1F
            return self._palettes[a]
        elif 0x2000 <= address:
            if 0x3000 <= address:
                a = (address - 0x1000) - 0x2000         # 映射 0x3000 - 0x3F00 到 0x2000 - 0x2EFF
            else:
                a = (address - 0x2000)
            a = self._address_from_mirror_type(a)
            return self._vram.read_byte(a)
        else:
            return self._cartridge.chr_rom[address]

    def _address_from_mirror_type(self, address):
        t = self._cartridge.mirroring_type
        if t is MirroringType.Horizontal:
            return (address & 0b0010_0011_1111_1111) | \
                   (0b0000_0100_0000_0000 if address & 0b0000_1000_0000_0000 else 0)
        elif t is MirroringType.Vertical:
            return address & 0x27FF
        elif t is MirroringType.Four_Screen:
            return address

    def read_name_table(self, address):
        address -= 0x2000
        return self._vram[address:address + 1024]

    def read_pattern_table(self, address):
        return self._cartridge.chr_rom[address:address + 0x1000]
