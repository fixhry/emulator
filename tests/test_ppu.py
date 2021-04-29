from cpu import CPU
from ppu import PPU
from memory.ram import RAM
from bus.cpu_bus import CPUBus
from bus.ppu_bus import PPUBus
from cartridge import Cartridge
from memory.palettes import palettes


def setup_ppu(rom_path):
    ppu = PPU()
    vram = RAM(0x1000)  # 4K
    background_palette = RAM(16)
    sprite_palette = RAM(16)
    cartridge = Cartridge(rom_path)
    ppu_bus = PPUBus(ppu, vram, cartridge, background_palette, sprite_palette)
    return ppu, ppu_bus


def test_ppu_bus():
    """
    读写 vram
    """
    rom = 'mario.nes'
    ppu, bus = setup_ppu(rom)


def test_ppu_registers():
    """
    读写寄存器
    """
    rom = 'balloon.nes'
    ppu, bus = setup_ppu(rom)

