from enum import Enum
import math
from PIL import Image

from memory import MemoryRead, MemoryWrite
from utils import *


class MirroringType(Enum):
    Horizontal = 0
    Vertical = 1
    Four_Screen = 2


width = 256
height = 240
image = Image.new('RGB', (width, height))


class PPU(MemoryRead, MemoryWrite):
    """
    PPU 渲染流程
    http://wiki.nesdev.com/w/index.php/PPU_rendering
    https://bugzmanov.github.io/nes_ebook/chapter_6_1.html
    http://wiki.nesdev.com/w/index.php/PPU_rendering#Line-by-line_timing

    The PPU renders 262 scanlines per frame. (0 - 240 are visible scanlines, the rest are so-called vertical overscan)
    Each scanline lasts for 341 PPU clock cycles, with each clock cycle producing one pixel. (the first 256 pixels are visible, the rest is horizontal overscan)
    The NES screen resolution is 320x240, thus scanlines 241 - 262 are not visible.
    """

    def __init__(self, vram):
        self._vram = vram

        self.nmi = False
        self._scanline = 0
        self._cycles = 0
        self._vblank_nmi = False

        self._setup_registers()
        self._setup_palettes()

        self._bus = None

    def read_register(self, address):
        """
        读写寄存器，和 VRAM 的读写方法不一样
        """
        if address == 0x2007:
            self._read_vram_address()
        i = address - 0x2000
        return self._registers[i]

    def write_register(self, address, data):
        if address == 0x2006:
            self._write_vram_address(data)
        i = address - 0x2000
        self._registers[i] = data

    def write_word(self, address, data):
        raise RuntimeError('方法调用错误 PPU.write_word address {} data {}'.format(hex(address), hex(data)))

    def read_word(self, address):
        raise RuntimeError('方法调用错误 PPU.read_word address {}'.format(hex(address)))

    def _read(self, address):
        return self._vram.read_byte(address)

    def _write(self, address, data):
        self._vram.write_byte(address, data)

    def _setup_registers(self):
        self._registers = [0] * 8
        # 用来模拟 2006 2007 的读写操作
        self._vram_cache = 0
        self._address_cache = []

    def _is_dummy_read(self):
        return len(self._address_cache) == 2

    def _update_vram_address(self):
        """
        每次从 0x2007 真正读出数据都要更新 0x2006 的地址
        """
        a = self.read_register(0x2000)
        i = 1 if ((a >> 2) & 1) == 0 else 32
        value = self.read_register(0x2006) + i
        self.write_register(0x2006, value)

    def _write_vram_address(self, byte):
        """
        CPU 写地址到 0x2006
        """
        self._address_cache.append(byte)

    def _read_vram_address(self):
        """
        CPU 从 0x2007 读数据
        """
        if self._is_dummy_read():
            d = self._vram_cache

            high, low = self._address_cache
            real_address = (high << 8) + low
            self._address_cache = []
            self._vram_cache = self.read_byte(real_address)
            self.write_register(0x2007, self._vram_cache)

            self._update_vram_address()

            return d
        else:
            return self._vram_cache

    @property
    def vblank_nmi(self):
        return self._vblank_nmi

    def clear_vblank_nmi(self):
        self._vblank_nmi = False

    def _set_vblank_nmi(self):
        self._vblank_nmi = True

    def _setup_palettes(self):
        """
        the image palette ($3F00-$3F0F) and the sprite palette ($3F10-$3F1F). The
        image palette shows the colours currently available for background tiles. The sprite palette
        shows the colours currently available for sprites
        """
        self.palettes = []

    def draw_tail(self, position, data):
        x = 0
        colors = [
            (0, 0, 0),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
        ]
        tail_w = 8
        tail_h = 8
        while x < tail_w:
            byte_low = data[x]
            byte_high = data[x + 8]
            y = 0
            while y < tail_h:
                c1 = (byte_low >> (7 - y)) & 1
                c2 = (byte_high >> (7 - y)) & 1
                pixel = (c2 << 1) + c1
                color = colors[pixel]
                x1, y1 = position
                x2 = x1 + x
                y2 = y1 + y
                p = (x2, y2)
                image.putpixel(p, color)
                y += 1
            x += 1

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
        width = 32
        height = 20
        pixel_width = 8
        # x y 第几个 tail
        x = 0
        while x < width:
            y = 0
            while y < height:
                i = (y * 4 + x) * 16
                data = self._vram.pattern_tables[i:i+16]
                x1 = x * 8
                y1 = y * 8
                self.draw_tail((x1, y1), data)
                y += 1
            x += 1
        # data = self._vram.pattern_tables[0x1000:0x1010]
        # data = self._vram.pattern_tables[0x00:0x10]
        # self.draw_tail(0, 0, data)
        # image.show()

    def draw_pattern_table(self):
        i = 0
        while i < 960:
            data = self._vram.pattern_tables[i:i+16]
            x = (i % 32)
            y = math.floor(i / 32)
            sx = x * 8
            sy = y * 8
            # log('tile index', x, y)
            self.draw_tile((sx, sy), data)
            i += 1
        image.show()

    def draw_tile(self, position, data):
        # log('draw tile start position', position)
        sx, sy = position
        x = 0

        colors = [
            (0, 0, 0),
            (255, 0, 0),
            (255, 255, 255),
            (135, 195, 235),
        ]
        while x < 8:
            byte_low = data[x]
            byte_high = data[x + 8]
            y = 0
            while y < 8:
                c1 = (byte_low >> (7 - y)) & 1
                c2 = (byte_high >> (7 - y)) & 1
                pixel = (c2 << 1) + c1
                color = colors[pixel]
                pixel_position = (sx + x, sy + y)
                # log('target position', pixel_position)
                image.putpixel(pixel_position, color)
                y += 1
            x += 1

    def draw(self):
        data = self._vram.pattern_tables[:10]
        # self.draw_pattern_table()
        # self.draw_background()

    def tick(self, cycles):
        """
        1 frame 262 scanline (0 ~ 261)
        1 scanline 341 PPU cycles
        1 cycle 1 pixel
        """
        self._cycles += (cycles * 3)
        if self._cycles % 341 == 0:
            self._scanline += 1

            if self._scanline == 241:
                self._trigger_vlank()

            if self._scanline >= 261:
                self._scanline = 0
                self._clear_vlank_status()

    def connect_to_bus(self, bus):
        self._bus = bus

    def _set_vlank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        status = self.read_register(0x2000)
        updated = status | 0x80
        self.write_register(0x2000, updated)

    def _clear_vlank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        status = self.read_register(0x2000)
        updated = status & 0x7F
        self.write_register(0x2000, updated)

    def _trigger_vlank(self):
        self._set_vlank_status()
        self._bus.trigger_vblank()
