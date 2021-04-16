from utils import *

import math
from PIL import Image


width = 256
height = 240
image = Image.new('RGB', (width, height))


class PPU:
    """
    PPU 渲染流程
    http://wiki.nesdev.com/w/index.php/PPU_rendering
    https://bugzmanov.github.io/nes_ebook/chapter_6_1.html

    The PPU renders 262 scanlines per frame. (0 - 240 are visible scanlines, the rest are so-called vertical overscan)
    Each scanline lasts for 341 PPU clock cycles, with each clock cycle producing one pixel. (the first 256 pixels are visible, the rest is horizontal overscan)
    The NES screen resolution is 320x240, thus scanlines 241 - 262 are not visible.
    """

    def __init__(self, vram,):
        self._vram = vram
        # self._cpu = cpu
        self._setup_palettes()

        self.nmi = False
        self._scanline = 0
        self._cycles = 0
        self._vblank_nmi = False

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

    def tick(self):
        self._cycles += 1
        if self._cycles % 341 == 0:
            self._scanline += 1

    def _trigger_vlank(self):
        self._set_vblank_nmi()

    def run(self):
        """
        PPU 渲染一帧画面需要做的事
        CYCLE_0
        FETCH_NAMETABLE,
        STORE_NAMETABLE,
        FETCH_ATTRIBUTE,
        STORE_ATTRIBUTE,
        FETCH_PATTERN_LOW,
        STORE_PATTERN_LOW,
        FETCH_PATTERN_HIGH,
        STORE_PATTERN_HIGH,
        WASTE_NAMETABLE_BYTE,
        POST_RENDER_SCANLINE,
        LOAD_SPRITES,
        FIRST_VBLANK_SCANLINE,
        IDLE_VBLANK_SCANLINES,
        PRE_RENDER_SCANLINE_START,
        LOAD_VERTICAL_SCROLL,
        WAIT_FOR_SCANLINE_TILE_FETCH,
        """
        if self._scanline == 241:
            self._trigger_vlank()
        self.tick()
