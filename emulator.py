from bus import Bus
from cpu import CPU
from ppu import PPU
from cartridge import Cartridge
from memory import RAM, VRAM
from utils import *


class Emulator:
    """
    each PPU frame takes 341*262=89342 PPU clocks cycles
    CPU is guaranteed to receive NMI every interrupt ~29780 CPU cycles
    """
    def __init__(self, rom_path):
        self._rom_path = rom_path
        self._cycles = 0
        self._setup()

    def _setup(self):
        cartridge = Cartridge(self._rom_path)
        size = cartridge.sram_bank * 8 * 1024
        sram = RAM(size)
        ram = RAM(0x0800)
        vram = VRAM(cartridge.chr_rom)
        IO_registers = RAM(0x20)
        self._ppu = PPU(vram)
        self._cpu = CPU()
        self._bus = Bus(self._cpu, self._ppu, ram, vram, sram, cartridge, IO_registers)

    def power(self):
        pass

    def run(self):
        """
        Catch-up
        http://wiki.nesdev.com/w/index.php/Catch-up
        """
        while True:
            self._cpu.emulate_once()
