from enum import Enum
import math
from PIL import Image

from utils import *

from memory.ram import RAM


class MirroringType(Enum):
    Horizontal = 0
    Vertical = 1
    Four_Screen = 2


width = 256
height = 240
image = Image.new('RGB', (width, height))


nametable = [36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 240, 241, 36, 36, 36, 36, 224, 225, 225,
             226, 224, 225, 225, 226, 224, 226, 36, 224, 226, 36, 224, 225, 225, 226, 224, 225, 225, 226, 224, 236, 36,
             224, 226, 36, 36, 36, 36, 36, 227, 227, 227, 229, 227, 227, 227, 229, 227, 229, 36, 227, 229, 36, 227, 227,
             227, 229, 227, 227, 227, 229, 227, 227, 243, 227, 229, 36, 36, 36, 36, 36, 227, 228, 227, 231, 227, 228,
             227, 229, 227, 229, 36, 227, 229, 36, 227, 228, 227, 229, 227, 228, 227, 229, 227, 227, 227, 227, 229, 36,
             36, 36, 36, 36, 227, 227, 227, 226, 227, 227, 227, 229, 227, 229, 36, 227, 229, 36, 227, 227, 227, 229,
             227, 227, 227, 229, 227, 227, 227, 227, 229, 36, 36, 36, 36, 36, 227, 228, 227, 229, 227, 242, 227, 229,
             227, 227, 226, 227, 227, 226, 227, 227, 227, 229, 227, 227, 227, 229, 227, 242, 227, 227, 229, 36, 36, 36,
             36, 36, 230, 227, 227, 231, 235, 36, 230, 231, 230, 227, 231, 230, 227, 231, 230, 227, 227, 231, 230, 227,
             227, 231, 235, 36, 230, 227, 231, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 224, 225,
             225, 226, 224, 226, 224, 225, 225, 226, 232, 36, 224, 226, 224, 225, 225, 226, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 227, 227, 227, 231, 227, 229, 227, 245, 246, 231, 227, 243, 227, 229, 230, 227,
             227, 231, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 227, 227, 239, 36, 227, 229, 227, 36, 36,
             36, 227, 227, 227, 229, 36, 227, 229, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 227, 227,
             225, 234, 227, 229, 227, 233, 227, 226, 227, 227, 227, 229, 36, 227, 229, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 227, 227, 239, 36, 227, 229, 227, 243, 227, 229, 227, 242, 227, 229, 36, 227,
             229, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 230, 231, 36, 36, 230, 231, 230, 231, 230,
             231, 235, 36, 230, 231, 36, 230, 231, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 10, 36, 36, 1, 37, 25, 21, 10, 34, 14, 27, 36, 16, 10, 22, 14, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 11, 36, 36, 2, 37, 25, 21, 10, 34, 14, 27, 36, 16,
             10, 22, 14, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 12, 36, 36,
             11, 10, 21, 21, 24, 24, 23, 36, 36, 29, 27, 18, 25, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 244, 1, 9, 8, 4, 36, 23, 18, 23,
             29, 14, 23, 13, 24, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36,
             36, 36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ]

oam = [240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 140, 168, 34, 44, 140, 169, 34, 52, 148, 170, 34, 48, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, 240, 0, 0, 0, ]


class PPU:
    """
    PPU 渲染流程
    http://wiki.nesdev.com/w/index.php/PPU_rendering
    https://bugzmanov.github.io/nes_ebook/chapter_6_1.html
    http://wiki.nesdev.com/w/index.php/PPU_rendering#Line-by-line_timing

    The PPU renders 262 scanlines per frame. (0 - 240 are visible scanlines, the rest are so-called vertical overscan)
    Each scanline lasts for 341 PPU clock cycles, with each clock cycle producing one pixel. (the first 256 pixels are visible, the rest is horizontal overscan)
    The NES screen resolution is 320x240, thus scanlines 241 - 262 are not visible.
    """

    def __init__(self):
        self._frame = 0
        self._scanline = 240
        self._cycle = 340
        self._nmi_delay = 0

        self._setup_registers()
        self._spr_ram = RAM(256)

        self._cpu_bus = None
        self._ppu_bus = None

    """
    寄存器
    """

    @property
    def control(self):
        return self._control

    @property
    def mask(self):
        return self._mask

    @property
    def status(self):
        return self._status

    @property
    def oam_address(self):
        return self._oam_address

    """
    标志位
    """

    @property
    def show_background(self):
        return ((self.mask >> 3) & 1) == 1

    @property
    def show_sprite(self):
        return ((self.mask >> 4) & 1) == 1

    @property
    def vblank_occurring(self):
        return (self.status & 0x80) > 0

    @property
    def nmi_enabled(self):
        return (self.control & 0x80) > 0

    @property
    def sprite_0_hit(self):
        return (self.status & 0x40) > 0

    @property
    def sprite_overflow(self):
        return (self.status & 0x20) > 0

    def _setup_registers(self):
        # 0x2000
        self._control = 0
        # 0x2001
        self._mask = 0
        # 0x2002
        self._status = 0
        # 0x2003
        self._oam_address = 0
        # 0x2007
        self._ppu_data = 0
        # ppu 内部寄存器
        self._vram_address = 0          # 15 bit
        self._tmp_vram_address = 0      # 15 bit
        self._fine_x = 0                # 3 bit
        self._write_toggle = 0          # 1 bit

        # 用来模拟 2006 2007 的读写操作
        self._vram_cache = 0
        # Least significant bits previously written into a PPU register
        self._prev_data = 0

    def _update_vram_address(self):
        """
        每次从 0x2007 读/写数据都要更新 0x2006 的地址
        """
        i = 1 if ((self._control >> 2) & 1) == 0 else 32
        self._vram_address += i
        self._vram_address &= 0x7FFF

    def _read_ppu_data(self):
        """
        CPU 从 0x2007 读数据
        """
        last_cache = self._vram_cache
        if self._vram_address >= 0x3F00:
            self._vram_cache = self._ppu_bus.read_byte(self._vram_address)
            self._update_vram_address()
            return self._vram_cache
        else:
            # 返回的是上一次读到的 vram 数据
            self._vram_cache = self._ppu_bus.read_byte(self._vram_address)
            self._update_vram_address()
            return last_cache

    def _write_ppu_data(self, data):
        # FIXME 这里的地址是相对 name tables 的偏移?
        # address = self._vram_address + 0x2000
        address = self._vram_address
        # log('v', hex(self._vram_address), 'address', hex(address))
        self._ppu_bus.write_byte(address, data)
        self._update_vram_address()

    def _write_ppu_address(self, data):
        t = self._tmp_vram_address
        if self._write_toggle == 0:
            self._tmp_vram_address = t & 0x80FF | (data & 0x3F) << 8
            self._write_toggle = 1
        else:
            self._tmp_vram_address = t & 0xFF00 | data
            self._vram_address = self._tmp_vram_address
            self._write_toggle = 0

    def _set_vblank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        updated = self.status | 0x80
        self._status = updated

    def _clear_vblank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        updated = self.status & 0x7F
        self._status = updated

    def _set_sprite_0_hit(self):
        updated = self.status | 0x40
        self._status = updated

    def _clear_sprite_0_hit(self):
        updated = self.status & 0x40
        self._status = updated

    def _set_sprite_overflow(self):
        updated = self.status | 0x20
        self._status = updated

    def _clear_sprite_overflow(self):
        updated = self.status & 0x20
        self._status = updated

    def _trigger_nmi(self):
        self._set_vblank_status()
        self._cpu_bus.trigger_vblank()

    def _pattern_address_table_from_controller(self):
        flag = (self._control >> 3) & 1
        address = 0x0 if flag is 0 else 0x1000
        return address

    def _name_table_address_from_controller(self):
        flag = self._control & 0x3
        address = (0x2000, 0x2400, 0x2800, 0x2C00)[flag]
        return address

    def _sprite_size_from_register(self):
        flag = (self._control >> 5) & 1
        size = (8, 16) if flag is 0 else (8, 16)
        return size

    def _name_table_from_vram(self):
        address = self._name_table_address_from_controller()
        return self._ppu_bus.read_name_table(address)

    def _pattern_table_from_vram(self):
        address = self._pattern_address_table_from_controller()
        return self._ppu_bus.read_pattern_table(address)

    def _read_ppu_status(self):
        data = self._status | self._prev_data
        self._clear_vblank_status()
        self._write_toggle = 0
        return data

    def _write_ppu_control(self, data):
        self._control = data
        self._tmp_vram_address = self._tmp_vram_address & 0xF3FF | (data & 0x03) << 10

    def _write_ppu_mask(self, data):
        self._mask = data

    def _write_oam_address(self, data):
        self._oam_address = data

    def _write_scroll(self, data):
        if self._write_toggle == 0:
            self._tmp_vram_address = self._tmp_vram_address & 0xFFE0 | data >> 3
            self._fine_x = data & 0x07
            self._write_toggle = 1
        else:
            self._tmp_vram_address = self._tmp_vram_address & 0x0C1F | (data & 0x07) << 12 | (data & 0xF8) << 2
            self._write_toggle = 0

    def _read_oam_data(self):
        return self._spr_ram.read_byte(self._oam_address)

    def connect_to_ppu_bus(self, bus):
        self._ppu_bus = bus

    def connect_to_cpu_bus(self, bus):
        self._cpu_bus = bus

    def read_register(self, address):
        """
        读写 ppu 寄存器
        """
        if address == 0x2000:
            return self._control
        if address == 0x2001:
            return self._mask
        if address == 0x2002:
            return self._status
        elif address == 0x2003:
            # OAM address
            return 0
        elif address == 0x2004:
            # OAM DATA
            return self._read_oam_data()
        elif address == 0x2005:
            # PPU scroll
            return 0
        elif address == 0x2006:
            # PPU address
            return 0
        elif address == 0x2007:
            # PPU DATA
            return self._read_ppu_data()

    def write_register(self, address, data):
        data &= 0xFF
        self._prev_data = data & 0x1F

        if address == 0x2000:
            # ppu control
            self._write_ppu_control(data)
        elif address == 0x2001:
            self._write_ppu_mask(data)
        elif address == 0x2003:
            self._write_oam_address(data)
        elif address == 0x2004:
            # oam data
            self._write_oam_data(data)
        elif address == 0x2005:
            self._write_scroll(data)
        elif address == 0x2006:
            # PPU address
            self._write_ppu_address(data)
        elif address == 0x2007:
            # 把数据写到 vram 中
            self._write_ppu_data(data)

    def _write_oam_data(self, data):
        address = self.oam_address & 0xFF
        self.write_spr_ram(address, data)
        # 更新 oam address
        self._oam_address += 1

    def write_spr_ram(self, address, data):
        log('write_spr_ram address {} data {}'.format(hex(address), hex(data)))
        self._spr_ram.write_byte(address, data)

    def sprite_color_from_table(self, index, table):
        # 大图块对应的字节
        j = math.floor(index / 4 / 16)
        # 中图块的序号
        v = table[j]
        k = math.floor(index / (4 * 8))
        z = (4 - k % 4) * 2
        index += 4
        color_index = v >> z & 0b11
        return color_index

    def draw_sprite(self):
        # TODO palette scroll 8 * 16
        pattern_table = self._pattern_table_from_vram()
        i = 0
        # log('spr ram', self._spr_ram)
        while i < self._spr_ram.size:
            s = self._spr_ram[i:i+4]
            # s = oam[i:i+4]
            x = s[3]
            y = s[0] + 1
            tail_index = s[1] * 16
            tail_data = pattern_table[tail_index:tail_index+16]
            self.draw_tile((x, y), tail_data)
            i += 4
        image.show()

    def draw_background(self):
        """
        pattern table 8KB 相当于存了两张 128 * 128 的图片

        0               4K              8K
            128 * 128       128 * 128

        tile 8 * 8 = 16B sprite 由多个 tile 组成
        每个 pattern table 可以存 256 个 tail
        每个 tail 16B 前 8B 低位 后 8B 高位 一个像素点可取得值 0(透明) 1 2 3

        Name Tables $03C0  960 Byte
        每字节控制
        """
        pattern_table = self._pattern_table_from_vram()
        name_table = self._name_table_from_vram()
        log('name_table', name_table)
        attribute_table = name_table[-64:]
        i = 0
        while i < 960:
            tail_index = name_table[i]
            # tail_index = nametable[i]
            start = tail_index * 16
            end = start + 16
            tail_data = pattern_table[start:end]
            tail_x = (i % 32)
            tail_y = math.floor(i / 32)
            palettes = self._background_palettes_from_attribute_table(attribute_table, tail_x, tail_y)
            self.draw_tile((tail_x*8, tail_y*8), tail_data)
            i += 1
        image.show()

    def _background_palettes_from_attribute_table(self, attribute_table, x, y):
        attr_table_idx = math.floor(x / 4) + math.floor(y / 4) * 8
        attr_byte = attribute_table[attr_table_idx]
        palette_index = (attr_byte >> (math.floor((x % 4) / 2) * 2 + math.floor((y % 4) / 2) * 4)) & 0b11
        palette_start = 1 + palette_index * 4
        return [
            self._ppu_bus.read_byte(0x3F00),
            self._ppu_bus.read_byte(palette_start+0x3F00),
            self._ppu_bus.read_byte(palette_start+0x3F00+1),
            self._ppu_bus.read_byte(palette_start+0x3F00+2),
        ]

    def draw_pattern_table(self):
        i = 0
        palettes = [
            (0, 0, 0),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
        ]
        while i < 512:
            start = i * 16
            end = start + 16
            data = self._ppu_bus._cartridge.chr_rom[start:end]
            x = (i % 32)
            y = math.floor(i / 32)
            sx = x * 8
            sy = y * 8
            self.draw_tile((sx, sy), data, palettes)
            i += 1
        image.show()

    def draw_tile(self, position, data, palettes=None):
        if palettes is None:
            palettes = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
        sx, sy = position
        y = 0
        while y < 8:
            byte_low = data[y + 8]
            byte_high = data[y]
            x = 0
            while x < 8:
                c1 = (byte_low >> (7 - x)) & 1
                c2 = (byte_high >> (7 - x)) & 1
                pixel = (c2 << 1) + c1
                color = palettes[pixel]
                px = sx + x
                py = sy + y
                if px <= width and py <= height:
                    image.putpixel((px, py), color)
                x += 1
            y += 1

    def draw(self):
        # self.draw_pattern_table()
        # self.draw_background()
        self.draw_sprite()

    def _update_cycle(self):
        if self.vblank_occurring and \
                self.nmi_enabled and \
                self._nmi_delay == 0:
            self._nmi_delay -= 1
            self._trigger_nmi()

        if self._cycle > 340:
            self._cycle = 0
            if self._scanline > 261:
                self._scanline = 0
                self._frame += 1
            self._scanline += 1

        if self._scanline == 241 and self._cycle == 1:
            self._set_vblank_status()

            if self.nmi_enabled:
                self._nmi_delay = 15

        if self._scanline == 261 and self._cycle == 1:
            self._clear_vblank_status()
            self._clear_sprite_0_hit()
            self._clear_sprite_overflow()

        self._cycle += 1

    def tick(self):
        """
        1 frame 262 scanline (0 ~ 261)
        1 scanline 341 PPU cycles
        1 cycle 1 pixel
        """
        if self._scanline == 261 and \
                self._cycle == 339 and \
                self._frame & 0x01 and \
                (self.show_background or self.show_sprite):
            self._update_cycle()

        self._update_cycle()

        if (not self.show_background) and (not self.show_sprite):
            return

        # 0 - 239: visible
        if 0 <= self._scanline <= 239:
            c = self._cycle

        # 240 - 260: Do nothing

        # 261: pre render
        if self._scanline == 261:
            pass

