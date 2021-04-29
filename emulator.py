from cpu import CPU
from ppu import PPU
from memory.ram import RAM
from bus.cpu_bus import CPUBus
from bus.ppu_bus import PPUBus
from cartridge import Cartridge
from memory.palettes import palettes


class Emulator:
    """
    each PPU frame takes 341*262=89342 PPU clocks cycles
    CPU is guaranteed to receive NMI every interrupt ~29780 CPU cycles
    """
    def __init__(self, rom_path):
        self._rom_path = rom_path
        self._cartridge = Cartridge(self._rom_path)
        self._setup_cpu_bus()
        self._setup_ppu_bus()
        self._cycles = 0
        self._counter = 0

    def _setup_cpu_bus(self):
        size = self._cartridge.sram_bank * 8 * 1024
        sram = RAM(size)
        ram = RAM(0x0800)
        IO_registers = RAM(0x20)
        self._ppu = PPU()
        self._cpu = CPU()
        self._cpu_bus = CPUBus(self._cpu, self._ppu, ram, sram, self._cartridge, IO_registers)

    def _setup_ppu_bus(self):
        vram = RAM(0x1000)  # 4K
        background_palette = RAM(16)
        sprite_palette = RAM(16)
        self._ppu_bus = PPUBus(self._ppu, vram, self._cartridge, background_palette, sprite_palette)

    def power(self):
        pass

    def run(self):
        """
        Catch-up
        http://wiki.nesdev.com/w/index.php/Catch-up
        """
        while self._counter <= 200000:
            self._cpu.emulate_once()
            self._counter += 1
            # log(self._counter)
        self._ppu.draw()
