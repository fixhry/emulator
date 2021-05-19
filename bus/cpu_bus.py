from memory.read import MemoryRead
from memory.write import MemoryWrite


class CPUBus(MemoryRead, MemoryWrite):
    def __init__(self, cpu, ppu, ram, sram, cartridge, joypad, IO_registers):
        self._ram = ram
        self._sram = sram
        self._cartridge = cartridge
        self._IO_registers = IO_registers
        self._joypad = joypad
        self._cpu = cpu
        self._cpu.connect_to_bus(self)
        self._ppu = ppu
        self._ppu.connect_to_cpu_bus(self)

    def trigger_nmi(self):
        self._cpu.handle_nmi()

    def _read(self, address):
        if 0x8000 <= address:
            a = address - 0x8000
            return self._cartridge.read_byte(a)
        elif 0x6000 <= address:
            return self._sram.read_byte(address - 0x6000)
        elif 0x4020 <= address:
            raise NotImplementedError('Expansion ROM 0x4020 - 0x6000 未实现')
        elif 0x4000 <= address:
            # 手柄
            if address == 0x4016:
                d = self._joypad.read()
                return d
            return self._IO_registers.read_byte(address - 0x4000)
        elif 0x2000 <= address:
            address &= 0x2007
            data = self._ppu.read_register(address)
            return data
        elif 0 <= address < 0x2000:
            a = address & 0x7FF
            return self._ram.read_byte(a)
        else:
            a = hex(address).upper()
            raise RuntimeError("内存越界 read at {}".format(a))

    def _write(self, address, data):
        if 0x8000 <= address:
            a = hex(address).upper()
            raise RuntimeError("Mapper 未实现 write.py at {}".format(a))
        elif 0x6000 <= address:
            a = address - 0x6000
            self._sram.write_byte(a, data)
        elif 0x4020 <= address:
            raise NotImplementedError('Expansion ROM 0x4020 - 0x6000 未实现')
        elif 0x4000 <= address:
            # 手柄
            if address == 0x4016:
                self._joypad.write(data)
            # DMA
            if address == 0x4014:
                start = data * 0x100
                spr_ram = self._ram[start:start+256]
                for i, e in enumerate(spr_ram):
                    self._ppu.write_spr_ram(i, e)
            self._IO_registers.write_byte(address - 0x4000, data)
        elif 0x2000 <= address:
            address &= 0x2007
            self._ppu.write_register(address, data)
        elif 0 <= address < 0x2000:
            address &= 0x7FF
            self._ram.write_byte(address, data)
        else:
            a = hex(address).upper()
            raise RuntimeError("内存越界 write.py at {}".format(a))
