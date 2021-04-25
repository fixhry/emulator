from memory import MemoryRead, MemoryWrite


class Bus(MemoryRead, MemoryWrite):
    """
    CPU 数据总线
    """
    def __init__(self, cpu, ppu, ram, vram, sram, cartridge, IO_registers):
        self._cpu = cpu
        self._cpu.connect_to_bus(self)
        self._ppu = ppu
        self._ppu.connect_to_bus(self)
        self._ram = ram
        self._vram = vram
        self._sram = sram
        self._cartridge = cartridge
        self._IO_registers = IO_registers

    def tick(self, cycles):
        """
        CPU 通知 PPU APU 执行，用于同步时钟周期

        :param cycles: CPU 执行指令后消耗的时钟周期
        """
        self._ppu.tick(cycles)

    def trigger_vblank(self):
        self._cpu.handle_vblank_interrupt()

    def _read(self, address):
        if 0x8000 <= address:
            a = address - 0x8000
            return self._cartridge.read_byte(a)
        elif 0x6000 <= address:
            return self._sram.read_byte(address - 0x6000)
        elif 0x4020 <= address:
            raise NotImplementedError('Expansion ROM 0x4020 - 0x6000 未实现')
        elif 0x4000 <= address:
            # TODO 外设
            return self._IO_registers.read_byte(address - 0x4000)
        elif 0x2000 <= address:
            return self._ppu.read_register(address)
        elif 0 <= address < 0x2000:
            a = address & 0x7FF
            return self._ram.read_byte(a)
        else:
            a = hex(address).upper()
            raise RuntimeError("内存越界 read at {}".format(a))

    def _write(self, address, data):
        if 0x8000 <= address:
            a = hex(address).upper()
            raise RuntimeError("Mapper 未实现 write at {}".format(a))
        elif 0x6000 <= address:
            a = address - 0x6000
            self._sram.write_byte(a, data)
        elif 0x4020 <= address:
            raise NotImplementedError('Expansion ROM 0x4020 - 0x6000 未实现')
        elif 0x4000 <= address:
            # TODO 外设
            self._IO_registers.write_byte(address - 0x4000, data)
        elif 0x2000 <= address:
            self._ppu.write_register(address, data)
        elif 0 <= address < 0x2000:
            address &= 0x7FF
            self._ram.write_byte(address, data)
        else:
            a = hex(address).upper()
            raise RuntimeError("内存越界 write at {}".format(a))
