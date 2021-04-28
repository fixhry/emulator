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

    @property
    def control(self):
        return self._registers[0]

    @property
    def mask(self):
        return self._registers[1]

    @property
    def status(self):
        return self._registers[2]

    @property
    def oam_address(self):
        return self._registers[3]

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
        self._registers = [0] * 8
        self._register = dict(
            v=0,
            t=0,
            x=0,
            w=0,
        )
        # 用来模拟 2006 2007 的读写操作
        self._vram_cache = 0
        self._address_cache = []
        # Least significant bits previously written into a PPU register
        self._prev_data = 0

    def _update_vram_address(self):
        """
        每次从 0x2007 读/写数据都要更新 0x2006 的地址
        """
        a = self.read_register(0x2000)
        i = 1 if ((a >> 2) & 1) == 0 else 32
        self._register['v'] += i
        self._register['v'] &= 0x7FFF

    def _read_ppu_data(self):
        """
        CPU 从 0x2007 读数据
        """
        # FIXME 这里的地址是相对 name tables 的偏移?
        v = self._register['v']
        last_cache = self._vram_cache
        if v >= 0x3F00:
            self._vram_cache = self._ppu_bus.read_byte(v)
            self._update_vram_address()
            return self._vram_cache
        else:
            # 返回的是上一次读到的 vram 数据
            self._vram_cache = self._ppu_bus.read_byte(v)
            return last_cache

    def _write_ppu_data(self, data):
        # FIXME 这里的地址是相对 name tables 的偏移?
        address = self._register['v']
        self._ppu_bus.write_byte(address, data)
        self._update_vram_address()

    def _write_ppu_address(self, data):
        t = self._register['t']
        if self._register['w'] == 0:
            self._register['t'] = t & 0x80FF | (data & 0x3F) << 8
        else:
            self._register['t'] = t & 0xFF00 | data
            self._register['v'] = self._register['t']
            self._register['w'] = 0

    def _set_vblank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        updated = self.status | 0x80
        self.write_register(0x2002, updated)

    def _clear_vblank_status(self):
        """
        The VBlank flag of the PPU is set at tick 1 (the second tick) of scanline 241
        """
        updated = self.status & 0x7F
        self.write_register(0x2002, updated)

    def _set_sprite_0_hit(self):
        updated = self.status | 0x40
        self.write_register(0x2002, updated)

    def _clear_sprite_0_hit(self):
        updated = self.status & 0x40
        self.write_register(0x2002, updated)

    def _set_sprite_overflow(self):
        updated = self.status | 0x20
        self.write_register(0x2002, updated)

    def _clear_sprite_overflow(self):
        updated = self.status & 0x20
        self.write_register(0x2002, updated)

    def _trigger_nmi(self):
        self._set_vblank_status()
        self._cpu_bus.trigger_vblank()

    def _pattern_address_table_from_controller(self):
        flag = (self.read_register(0x2000) >> 3) & 1
        address = 0x0 if flag is 0 else 0x1000
        return address

    def _name_table_address_from_controller(self):
        flag = self.read_register(0x2000) & 0x3
        address = (0x2000, 0x2400, 0x2800, 0x2C00)[flag]
        return address

    def _sprite_size_from_register(self):
        flag = (self.read_register(0x2000) >> 5) & 1
        size = (8, 16) if flag is 0 else (8, 16)
        return size

    def _name_table_from_vram(self):
        address = self._name_table_address_from_controller()
        return self._ppu_bus.read_name_table(address)

    def _pattern_table_from_vram(self):
        address = self._pattern_address_table_from_controller()
        return self._ppu_bus.read_pattern_table(address)

    def _read_ppu_status(self):
        data = self._registers[2] | self._prev_data
        self._clear_vblank_status()
        self._register['w'] = 0
        return data

    def _write_ppu_control(self, address, data):
        self._registers[address - 0x2000] = data
        self._register['t'] = self._register['t'] & 0xF3FF | (data & 0x03) << 10

    def _write_scroll(self, data):
        if self._register['w'] == 0:
            self._register['t'] = self._register['t'] & 0xFFE0 | data >> 3
            self._register['x'] = data & 0x07
            self._register['w'] = 1
        else:
            self._register['t'] = self._register['t'] & 0x0C1F | (data & 0x07) << 12 | (data & 0xF8) << 2
            self._register['w'] = 0

    def connect_to_ppu_bus(self, bus):
        self._ppu_bus = bus

    def connect_to_cpu_bus(self, bus):
        self._cpu_bus = bus

    def read_register(self, address):
        """
        读写寄存器，和 VRAM 的读写方法不一样
        """
        if address == 0x2002:
            # status
            return self._read_ppu_status()
        elif address == 0x2003:
            # OAM address
            return 0
        elif address == 0x2004:
            # OAM DATA
            oam_address = self._register[3]
            return self._spr_ram.read_byte(oam_address)
        elif address == 0x2005:
            # PPU scroll
            return 0
        elif address == 0x2006:
            # PPU address
            return 0
        elif address == 0x2007:
            # PPU DATA
            return self._read_ppu_data()
        else:
            return self._registers[address - 0x2000]

    def write_register(self, address, data):
        data &= 0xFF
        self._prev_data = data & 0x1F
        if address == 0x2000:
            # ppu control
            self._write_ppu_control(address, data)
        # elif address == 0x2002:
        #     # ppu status 只读
        #     pass
        elif address == 0x2004:
            # oam data
            self._write_oam(data)
        if address == 0x2005:
            self._write_scroll(data)
        if address == 0x2006:
            # PPU address
            self._write_ppu_address(data)
        if address == 0x2007:
            # 把数据写到 vram 中
            self._write_ppu_data(data)
        else:
            self._registers[address - 0x2000] = data

    def _write_oam(self, data):
        self.write_spr_ram(self.oam_address, data)
        # 更新 oam address
        self._registers[3] += 1

    def write_spr_ram(self, address, data):
        self._spr_ram.write_byte(address, data)

    def write_word(self, address, data):
        raise RuntimeError('方法调用错误 PPU.write_word address {} data {}'.format(hex(address), hex(data)))

    def read_word(self, address):
        raise RuntimeError('方法调用错误 PPU.read_word address {}'.format(hex(address)))

    def draw_tail(self, position, data):
        x = 0
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
                color = self._ppu_bus._palettes[pixel]
                x1, y1 = position
                x2 = x1 + x
                y2 = y1 + y
                p = (x2, y2)
                image.putpixel(p, color)
                y += 1
            x += 1

    def fomatted_nametable(self, nametable):
        z = 0
        t = nametable

        o = []

        i = 0
        while i < 240:
            j = 0
            while j < 256:
                # y
                o.append(i - 1)

                # index
                k = t[z]

                o.append(k)
                z += 1

                # tmp
                o.append(0)

                # x
                o.append(j)
                j += 8
            i += 8
        return o

    # def draw_sprite(self, oam_data, sprite_data):
    #     t = nametable()


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
        n = self.fomatted_nametable(name_table)
        log('name_table', name_table)
        property_table = name_table[-64:]
        # i = 0
        # while i < 960:
        #     start = i * 16
        #     end = start + 16
        #     data = self._vram.pattern_tables[start:end]
        #     x = (i % 32)
        #     y = math.floor(i / 32)
        #     sx = x * 8
        #     sy = y * 8
        #     # log('tile index', x, y)
        #     self.draw_tile((sx, sy), data)
        #     i += 1
        # image.show()

    def draw_pattern_table(self):
        i = 0
        while i < 512:
            start = i * 16
            end = start + 16
            data = self._ppu_bus._cartridge.chr_rom[start:end]
            x = (i % 32)
            y = math.floor(i / 32)
            sx = x * 8
            sy = y * 8
            self.draw_tile((sx, sy), data)
            i += 1
        image.show()

    def draw_tile(self, position, data):
        sx, sy = position
        colors = [
            (0, 0, 0),
            (255, 0, 0),
            (255, 255, 255),
            (135, 195, 235),
        ]
        y = 0
        while y < 8:
            byte_low = data[y + 8]
            byte_high = data[y]
            x = 0
            while x < 8:
                c1 = (byte_low >> (7 - x)) & 1
                c2 = (byte_high >> (7 - x)) & 1
                pixel = (c2 << 1) + c1
                # color = self._vram.palettes[pixel]
                color = colors[pixel]
                pixel_position = (sx + x, sy + y)

                # log('target position', pixel_position)
                image.putpixel(pixel_position, color)
                x += 1
            y += 1

    def draw(self):
        self.draw_pattern_table()
        # self.draw_background()

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

