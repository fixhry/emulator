from emulator import Emulator


def test_exec():
    rom = 'nestest.nes'
    emu = Emulator(rom)

    emu.run()
