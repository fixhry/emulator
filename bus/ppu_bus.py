from memory.read import MemoryRead
from memory.write import MemoryWrite
from ppu import MirroringType


class PPUBus(MemoryRead, MemoryWrite):
    def __init__(self, ppu, vram, cartridge, background_palette, sprite_palette):
        self._vram = vram
        self._cartridge = cartridge
        self._background_palette = background_palette
        self._sprite_palette = sprite_palette
        self._ppu = ppu
        self._ppu.connect_to_ppu_bus(self)

    def _write(self, address, data):
        address &= 0x3FFF

        if address < 0x2000:
            raise NotImplementedError('ppu write address {} data {}'.format(hex(address), hex(data)))
        elif address < 0x3000:
            a = self._address_from_mirror_type(address) - 0x2000
            self._vram.write_byte(a, data)
        elif address < 0x3F00:
            self._write(address-0x1000, data)
        else:
            address &= 0x3F1F

            if address < 0x3F10:
                self._background_palette.write_byte(address-0x3F00, data)
            else:
                if not (address & 0b11):
                    address -= 0x10
                    self._background_palette.write_byte(address-0x3F00, data)

                self._sprite_palette.write_byte(address-0x3F10, data)

    def _read(self, address):
        address &= 0x3FFF                               # 映射 0x4000 - 0xFFFF 到 0x0000 - 0x3FFF
        if address < 0x2000:
            return self._cartridge.chr_rom[address]
        elif address < 0x3000:
            a = self._address_from_mirror_type(address) - 0x2000
            return self._vram.read_byte(a)
        elif address < 0x3F00:
            self._read(address-0x1000)
        else:
            address &= 0x3F1F

            if address < 0x3F10:
                return self._background_palette.read_byte(address-0x3F00)
            else:
                # Addresses $3F10/$3F14/$3F18/$3F1C are mirrors of $3F00/$3F04/$3F08/$3F0C
                # https://wiki.nesdev.com/w/index.php/PPU_palettes
                if not (address & 0b11):
                    address -= 0x10
                    self._background_palette.read_byte(address-0x3F00)

                return self._sprite_palette.read_byte(address-0x3F10)

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
