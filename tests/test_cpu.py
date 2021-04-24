from bus import Bus
from cpu import CPU
from ppu import PPU
from cartridge import Cartridge
from memory import RAM, VRAM
from utils import *


def setup_bus():
    file_name = 'nestest.nes'
    cartridge = Cartridge(file_name)
    size = cartridge.sram_bank * 8 * 1024
    sram = RAM(size)
    ram = RAM(0x0800)
    vram = VRAM(cartridge.chr_rom)
    IO_registers = RAM(0x20)
    ppu = PPU(vram)
    bus = Bus(ppu, ram, vram, sram, cartridge, IO_registers)
    return bus, vram, ppu


def test_exec():
    bus, vram, ppu = setup_bus()
    cpu = CPU(bus)
    cpu.run()
