from enum import Enum
import math

from memory.ram import RAM
from memory.palettes import palettes


class MirroringType(Enum):
    Horizontal = 0
    Vertical = 1
    Four_Screen = 2


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
        self.frame_ready = False
        self.frame_buffer = [(0, 0, 0)] * 256 * 240

        self._setup_registers()
        self._spr_ram = RAM(256)
        self._sprite_pixels = [0] * 256
        self._pixels = [0] * (256 * 240)

        self._cpu_bus = None
        self._ppu_bus = None

    @property
    def cycle(self):
        return self._cycle

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
    def show_background_left(self):
        """
        Bit 1 - Specifies whether to clip the background, that is
        whether to hide the background in the left 8 pixels on
        screen (0) or to show them (1).
        """
        return ((self.mask >> 1) & 1) == 1

    @property
    def show_sprite_left(self):
        """
        Specifies whether to clip the sprites, that is whether
        to hide sprites in the left 8 pixels on screen (0) or to show them (1).
        """
        return ((self.mask >> 2) & 1) == 1

    @property
    def vblank_occurring(self):
        return ((self.status >> 7) & 1) == 1

    @property
    def sprite_0_hit(self):
        return ((self.status >> 6) & 1) == 1

    @property
    def sprite_overflow(self):
        return ((self.status >> 5) & 1) == 1

    @property
    def nmi_enabled(self):
        return ((self.control >> 7) & 1) == 1

    @property
    def background_pattern_table_address(self):
        flag = (self._control >> 4) & 1
        address = 0x0 if flag is 0 else 0x1000
        return address

    @property
    def sprite_pattern_table_address(self):
        flag = (self._control >> 3) & 1
        address = 0x0 if flag is 0 else 0x1000
        return address

    @property
    def sprite_size(self):
        flag = (self._control >> 5) & 1
        size = 8 if flag is 0 else 16
        return size

    @property
    def name_table_address(self):
        flag = self._control & 0x3
        address = (0x2000, 0x2400, 0x2800, 0x2C00)[flag]
        return address

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
        self._vram_address = 0  # 15 bit
        self._tmp_vram_address = 0  # 15 bit
        self._fine_x = 0  # 3 bit
        self._write_toggle = 0  # 1 bit

        # 用来模拟 2006 2007 的读写操作
        self._vram_cache = 0
        # Least significant bits previously written into a PPU register
        self._prev_data = 0

        # shift
        self._shift_low_background_tail_bytes = 0
        self._shift_high_background_tail_bytes = 0
        self._shift_low_background_attribute_bytes = 0
        self._shift_high_background_attribute_bytes = 0

        # latches
        self._latches_name_table = 0
        self._latches_attribute_table = 0
        self._latches_low_background_tail_byte = 0
        self._latches_high_background_tail_byte = 0

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
        address = self._vram_address
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
        updated = self.status & 0xBF
        self._status = updated

    def _set_sprite_overflow(self):
        updated = self.status | 0x20
        self._status = updated

    def _clear_sprite_overflow(self):
        updated = self.status & 0xDF
        self._status = updated

    def _trigger_nmi(self):
        self._cpu_bus.trigger_nmi()

    def _name_table_from_vram(self):
        return self._ppu_bus.read_name_table(self.name_table_address)

    def _pattern_table_from_vram(self, address):
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
            return self._read_ppu_status()
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
        self._spr_ram.write_byte(address, data)

    def _sprite_palette_from_oam(self, attribute):
        index = attribute & 0b11
        start = 0x11 + index * 4
        return [
            palettes[self._ppu_bus.read_byte(0x3F00)],
            palettes[self._ppu_bus.read_byte(0x3F00 + start)],
            palettes[self._ppu_bus.read_byte(0x3F00 + start + 1)],
            palettes[self._ppu_bus.read_byte(0x3F00 + start + 2)],
        ]

    def draw_sprite(self):
        # TODO scroll 8 * 16
        pattern_table = self._pattern_table_from_vram(self.sprite_pattern_table_address)
        i = 0
        while i < self._spr_ram.size:
            s = self._spr_ram[i:i + 4]
            x = s[3]
            y = s[0] + 1
            tail_index = s[1] * 16
            tail_data = pattern_table[tail_index:tail_index + 16]
            attribute = s[2]
            palette = self._sprite_palette_from_oam(attribute)
            if 0 < x < 256 and 0 < y < 240:
                self.draw_tile((x, y), tail_data, palette)
            i += 4

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
        pattern_table = self._pattern_table_from_vram(self.background_pattern_table_address)
        name_table = self._name_table_from_vram()
        attribute_table = name_table[-64:]
        i = 0
        while i < 960:
            tail_index = name_table[i]
            start = tail_index * 16
            end = start + 16
            tail_data = pattern_table[start:end]
            tail_x = (i % 32)
            tail_y = math.floor(i / 32)
            palette = self._background_palette_from_attribute_table(attribute_table, tail_x, tail_y)
            self.draw_tile((tail_x * 8, tail_y * 8), tail_data, palette)
            i += 1

    def _background_palette_from_attribute_table(self, attribute_table, x, y):
        """
        根据坐标求出当前 tile 属于哪个 block
        取出 block 在属性表中的 byte
        根据坐标求出当前 tile 在 block 中的 index
        用 index 取出调色板
        """
        attribute_index = math.ceil(x / 32) + math.ceil(y / 32) * 8
        attribute_data = attribute_table[attribute_index]
        tile_index = math.floor((x % 32) / 16) * 2 + math.floor((y % 32) / 16)
        palette_index = (attribute_data >>
                         ((0, 4, 2, 6)[tile_index])) & 0b11
        palette = [palettes[self._ppu_bus.read_byte(0x3F00)]]
        if palette_index == 0:
            return palette + [palettes[self._ppu_bus.read_byte(0x3F01)], palettes[self._ppu_bus.read_byte(0x3F02)], palettes[self._ppu_bus.read_byte(0x3F03)]]
        elif palette_index == 1:
            return palette + [palettes[self._ppu_bus.read_byte(0x3F05)], palettes[self._ppu_bus.read_byte(0x3F06)], palettes[self._ppu_bus.read_byte(0x3F07)]]
        elif palette_index == 2:
            return palette + [palettes[self._ppu_bus.read_byte(0x3F09)], palettes[self._ppu_bus.read_byte(0x3F0A)], palettes[self._ppu_bus.read_byte(0x3F0B)]]
        elif palette_index == 3:
            return palette + [palettes[self._ppu_bus.read_byte(0x3F0D)], palettes[self._ppu_bus.read_byte(0x3F0E)], palettes[self._ppu_bus.read_byte(0x3F0F)]]
        else:
            raise RuntimeError('palette_index', palette_index)

    def draw_tile(self, position, data, palette):
        sx, sy = position
        y = 0
        while y < 8:
            byte_low = data[y]
            byte_high = data[y + 8]
            x = 0
            while x < 8:
                c1 = (byte_low >> (7 - x)) & 1
                c2 = (byte_high >> (7 - x)) & 1
                i = (c2 << 1) + c1
                color = palette[i]
                px = sx + x
                py = sy + y
                index = py * 256 + px
                if 0 < px < 256 and 0 < py < 240:
                    self.frame_buffer[index] = color
                x += 1
            y += 1

    def log(self):
        return [
            self._cycle,
            self._scanline,
            self._control,
            self._mask,
            self._status,
            self._vram_address,
            self._tmp_vram_address,
            self._fine_x,
            self._write_toggle,
        ]

    def _update_vblank_status(self):
        if self._scanline == 241 and self._cycle == 1:
            self._set_vblank_status()
            if self.nmi_enabled:
                self._trigger_nmi()

        if self._scanline == 261 and self._cycle == 1:
            self._clear_vblank_status()
            self._clear_sprite_0_hit()
            self._clear_sprite_overflow()

    def _update_cycle(self):
        self._cycle += 1

        if self._cycle > 340:
            self._cycle = 0
            self._scanline += 1
            if self._scanline > 261:
                self._scanline = 0
                self._frame += 1
                # log('frame', self._frame)
                self.frame_ready = True
                self.draw_background()
                self.draw_sprite()

        self._update_vblank_status()

    def tick(self):
        """
        1 frame 262 scanline (0 ~ 261)
        1 scanline 341 PPU cycles
        1 cycle 1 pixel
        """
        self._update_cycle()

        if (not self.show_background) and (not self.show_sprite):
            return
