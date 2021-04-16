from memory import Memory
from cpu import CPU
from utils import *


class Emulator:
    """
    each PPU frame takes 341*262=89342 PPU clocks cycles
    CPU is guaranteed to receive NMI every interrupt ~29780 CPU cycles
    """
    def __init__(self, cpu, ppu):
        self._cpu = cpu
        self._ppu = ppu
        self._cycles = 0

    def _tick(self):
        self._cycles += 1

    def exec_cpu(self):
        cond = self._cycles % 3 == 0
        if cond:
            self._cpu.tick()

    def exec_ppu(self):
        self._ppu.tick()

    def _loop(self):
        """
        1s 大概
        """
        pass

    def power(self):
        pass

    def run(self):
        while self._cycles < 89342:
            log('emu', self._cycles)
            self.exec_ppu()
            self.exec_cpu()
            if self._ppu.vblank_nmi is True:
                self._cpu.handle_interrupt()
                self._ppu.clear_vblank_nmi()
            self._tick()
