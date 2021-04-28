from ppu import MirroringType
from memory.read import MemoryRead


class Cartridge(MemoryRead):
    """
    nes 文件格式
    https://zhuanlan.zhihu.com/p/34636695
    """
    def __init__(self, file_name):
        self._file_name = file_name
        self._setup_cartridge()

    def __repr__(self):
        s = f"""<{self._file_name}
        PRG ROM 块数 {self._prg_banks}
        CHR ROM 块数 {self._chr_banks}
        SRAM 块数    {self._sram_banks}
        Mirroring   {self._mirroring_type}
        mapper      {self._mapper_type}
        has trainer {self._has_trainer}
        battery backed {self._battery_backed}>
        """
        return s

    @property
    def chr_rom(self):
        return self._chr_rom

    @property
    def prg_rom(self):
        return self._prg_rom

    @property
    def prg_banks(self):
        """
        PRG ROM 块每个大小为 16KB
        """
        return self._prg_banks

    @property
    def chr_banks(self):
        """
        CHR ROM 块每个大小为 8 KB
        """
        return self._chr_banks

    @property
    def mapper_type(self):
        return self._mapper_type

    @property
    def sram_bank(self):
        return self._sram_banks

    @property
    def mirroring_type(self):
        return self._mirroring_type

    def _load_nes_file(self):
        with open(self._file_name, 'rb') as f:
            self._file_data = list(f.read())
            if bytearray(self._file_data[:4]) != b"NES\x1a":
                raise RuntimeError("NES 文件格式错误!")

    def _setup_mapper(self):
        if self._prg_banks == 1:
            self._address_mask = 0x3FFF
        else:
            self._address_mask = 0xFFFF

    def _read(self, address):
        return self._prg_rom[address & self._address_mask]

    def _read_prg_byte(self, address):
        return super().read_byte(address)

    def _write(self, address, value):
        raise NotImplementedError(f"address ({hex(address)}) 写入 value ({hex(value)})")

    def _setup_cartridge(self):
        self._load_nes_file()
        self._data_from_nes_file()
        self._setup_mapper()

    def _setup_mapper_type(self):
        d = self._file_data
        mapper_low = (d[6] >> 4) & 0b1111
        mapper_high = (d[7] >> 4) & 0b1111
        n = (mapper_high << 4) + mapper_low
        if n == 0:
            self._mapper_type = 'NROM'
        else:
            self._mapper_type = 'Unknown'
            raise RuntimeError("未实现的 Mapper {}".format(n))

    def _setup_mirror_type(self):
        d = self._file_data[6]
        if d & (1 << 3):
            self._mirroring_type = MirroringType.FourScreen
        elif d & 1:
            self._mirroring_type = MirroringType.Vertical
        else:
            self._mirroring_type = MirroringType.Horizontal

    def _setup_sram_banks(self):
        """
        ram 块数 每块为 8KB，如果为 0 ，则假设只有一个 RAM 块
        """
        d = self._file_data[8]
        self._sram_banks = 1 if d is 0 else d

    def _setup_prg_banks(self):
        self._prg_banks = self._file_data[4]

    def _setup_chr_banks(self):
        self._chr_banks = self._file_data[5]

    def _setup_other_info(self):
        self._battery_backed = True if self._file_data[6] & 2 else False
        self._has_trainer = True if self._file_data[6] & 4 else False

    def _setup_rom(self):
        d = self._file_data
        prg_size = 16 * 1024 * self.prg_banks
        self._prg_rom = d[16:prg_size + 16]
        self._chr_rom = d[16 + prg_size:]

    def _data_from_nes_file(self):
        self._setup_mirror_type()
        self._setup_sram_banks()
        self._setup_mapper_type()
        self._setup_prg_banks()
        self._setup_chr_banks()
        self._setup_other_info()
        self._setup_rom()
