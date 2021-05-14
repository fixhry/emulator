from ppu import PPU
from bus.ppu_bus import PPUBus
from memory.ram import RAM
from emulator import Emulator
from cartridge import Cartridge


def test_write_palette():
    rom = 'balloon.nes'
    ppu = PPU()
    cartridge = Cartridge(rom)
    vram = RAM(0x1000)  # 4K
    background_palette = RAM(16)
    sprite_palette = RAM(16)
    bus = PPUBus(ppu, vram, cartridge, background_palette, sprite_palette)
    d1 = 1
    d2 = 2
    d3 = 3
    bus.write_byte(0x3F00, d1)
    bus.write_byte(0x3F01, d2)
    bus.write_byte(0x3F11, d3)
    v1 = bus.read_byte(0x3F00)
    v2 = bus.read_byte(0x3F01)
    v3 = bus.read_byte(0x3F11)
    assert d1 == v1, d1
    assert d2 == v2, d2
    assert d3 == v3, d3


def test_exec():
    rom = 'balloon.nes'
    emu = Emulator(rom)
    # emu.run()
