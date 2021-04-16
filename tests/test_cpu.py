from memory import *
from cpu import *
from memory import *
from cartridge import Cartridge
from ppu import *
from emulator import Emulator
from utils import *

m = RAM()
cart = Cartridge()
vram = VRAM(cart)
ppu = PPU(vram)
cpu = CPU(m, ppu)
emu = Emulator(cpu, ppu)


def test_exec():
    # emu.run()
    cpu.run()

