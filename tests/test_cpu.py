from bus import Bus
from cpu import CPU
from ppu import PPU
from cartridge import Cartridge
from memory import RAM, VRAM
from utils import *


def setup_bus():
    file_name = 'mario.nes'
    cartridge = Cartridge(file_name)
    log(cartridge)
    size = cartridge.sram_bank * 8 * 1024
    sram = RAM(size)
    ram = RAM(0x0800)
    vram = VRAM(cartridge.chr_rom)
    IO_registers = RAM(0x20)
    ppu = PPU(vram)
    cpu = CPU()
    bus = Bus(cpu, ppu, ram, vram, sram, cartridge, IO_registers)
    ppu.draw()
    return cpu


def test_exec():
    cpu = setup_bus()
    # cpu.run()
