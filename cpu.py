import time


from utils import *


def load_nestest_log():
    with open('f_nestest.json', 'r') as f:
        d = f.read()
        j = json.loads(d)
    return j


log_list = load_nestest_log()


def log_diff(index, output, logs):
    expected = logs[index]
    o = output
    # o = output.split(' ')
    tail = expected[-1]
    expected.pop()
    expected.pop()
    expected.append(tail)
    msg = """
        -------- {} -----------
        -------- output -------
        {}
        -------- expected ------
        {}
    """.format(index, o, expected)
    for i, s in enumerate(o):
        e = expected[i]
        assert e == s, msg


class CPU:
    """
    中断
        The addresses to jump to when an interrupt occurs are stored in a vector table in
        the program code at $FFFA-$FFFF. When an interrupt occurs the system performs the
        following actions:
    """

    def __init__(self):
        self._setup_instruction_set()
        self._setup_status_flags()
        self._bus = None

        # 操作数
        self._opcode = None
        self._operand = None
        self._cycles = 0
        # 执行当前指令需要消耗的 CPU 周期
        self._cycles_costs = 0
        self._current_instruction = None
        # debug
        self.debug = True
        self._count = 0

    @property
    def cycles(self):
        return self._cycles

    @property
    def instruction_set(self):
        """
        指令集
        56 种指令 151 valid opcodes
        """
        return self._instruction_set

    @property
    def program_counter(self):
        return self._register_pc

    @property
    def stack_pointer(self):
        return self._register_sp

    @property
    def accumulator(self):
        return self._register_a

    @property
    def index_x(self):
        return self._register_x

    @property
    def index_y(self):
        return self._register_y

    @property
    def status(self):
        v = ((self._flag_c << 0) +
             (self._flag_z << 1) +
             (self._flag_i << 2) +
             (self._flag_d << 3) +
             (self._flag_b << 4) +
             (1 << 5) +
             (self._flag_v << 6) +
             (self._flag_n << 7))
        return v

    def _setup_instruction_set(self):
        self._instruction_set = dict()
        i = self._instruction_set
        # 操作 寻址模式 指令名 寻址模式 指令长度 CPU 周期
        i[0x69] = (self._adc, self._address_imm, 'ADC', 'IMM', 2, 2)
        i[0x65] = (self._adc, self._address_zp, 'ADC', 'ZP', 2, 3)
        i[0x75] = (self._adc, self._address_zp_x, 'ADC', 'ZPX', 2, 4)
        i[0x6D] = (self._adc, self._address_abs, 'ADC', 'ABS', 3, 4)
        i[0x7D] = (self._adc, self._address_abs_x, 'ADC', 'ABX', 3, 4)
        i[0x79] = (self._adc, self._address_abs_y, 'ADC', 'ABY', 3, 4)
        i[0x61] = (self._adc, self._address_inx, 'ADC', 'INX', 2, 6)
        i[0x71] = (self._adc, self._address_iny, 'ADC', 'INY', 2, 5)

        i[0xA9] = (self._lda, self._address_imm, 'LDA', 'IMM', 2, 2)
        i[0xA5] = (self._lda, self._address_zp, 'LDA', 'ZP', 2, 3)
        i[0xB5] = (self._lda, self._address_zp_x, 'LDA', 'ZPX', 2, 4)
        i[0xAD] = (self._lda, self._address_abs, 'LDA', 'ABS', 3, 4)
        i[0xBD] = (self._lda, self._address_abs_x, 'LDA', 'ABX', 3, 4)
        i[0xB9] = (self._lda, self._address_abs_y, 'LDA', 'ABY', 3, 4)
        i[0xA1] = (self._lda, self._address_inx, 'LDA', 'INX', 2, 6)
        i[0xB1] = (self._lda, self._address_iny, 'LDA', 'INY', 2, 5)

        i[0x10] = (self._bpl, self._address_rel, 'BPL', 'REL', 2, 2)
        i[0x78] = (self._sei, self._address_imp, 'SEI', 'IMP', 1, 2)
        i[0xD8] = (self._cld, self._address_imp, 'CLD', 'IMP', 1, 2)
        i[0x58] = (self._cli, self._address_imp, 'CLI', 'IMP', 1, 2)
        i[0xB8] = (self._clv, self._address_imp, 'CLV', 'IMP', 1, 2)

        i[0xA2] = (self._ldx, self._address_imm, 'LDX', 'IMM', 2, 2)
        i[0xA6] = (self._ldx, self._address_zp, 'LDX', 'ZP', 2, 3)
        i[0xB6] = (self._ldx, self._address_zp_y, 'LDX', 'ZPY', 2, 4)
        i[0xAE] = (self._ldx, self._address_abs, 'LDX', 'ABS', 3, 4)
        i[0xBE] = (self._ldx, self._address_abs_y, 'LDX', 'ABY', 3, 4)

        i[0x9A] = (self._txs, self._address_imp, 'TXS', 'IMP', 1, 2)

        i[0x85] = (self._sta, self._address_zp, 'STA', 'ZP', 2, 3)
        i[0x95] = (self._sta, self._address_zp_x, 'STA', 'ZPX', 2, 4)
        i[0x8D] = (self._sta, self._address_abs, 'STA', 'ABS', 3, 4)
        i[0x9D] = (self._sta, self._address_abs_x_write, 'STA', 'ABX', 3, 5)
        i[0x99] = (self._sta, self._address_abs_y_write, 'STA', 'ABY', 3, 5)
        i[0x81] = (self._sta, self._address_inx, 'STA', 'INX', 2, 6)
        i[0x91] = (self._sta, self._address_iny, 'STA', 'INY', 2, 6)

        i[0xE8] = (self._inx, self._address_imp, 'INX', 'IMP', 1, 2)

        i[0xD0] = (self._bne, self._address_rel, 'BNE', 'REL', 2, 2)
        i[0x8A] = (self._txa, self._address_imp, 'TXA', 'IMP', 1, 2)
        i[0x20] = (self._jsr, self._address_abs, 'JSR', 'ABS', 3, 6)
        i[0xF0] = (self._beq, self._address_rel, 'BEQ', 'REL', 2, 2)

        i[0xE0] = (self._cpx, self._address_imm, 'CPX', 'IMM', 2, 2)
        i[0xE4] = (self._cpx, self._address_zp, 'CPX', 'ZP', 2, 3)
        i[0xEC] = (self._cpx, self._address_abs, 'CPX', 'ABS', 3, 4)

        i[0xB0] = (self._bcs, self._address_rel, 'BCS', 'REL', 2, 2)
        i[0x30] = (self._bmi, self._address_rel, 'BMI', 'REL', 2, 2)

        i[0xA0] = (self._ldy, self._address_imm, 'LDY', 'IMM', 2, 2)
        i[0xA4] = (self._ldy, self._address_zp, 'LDY', 'ZP', 2, 3)
        i[0xB4] = (self._ldy, self._address_zp_x, 'LDY', 'ZPX', 2, 4)
        i[0xAC] = (self._ldy, self._address_abs, 'LDY', 'ABS', 3, 4)
        i[0xBC] = (self._ldy, self._address_abs_x, 'LDY', 'ABX', 3, 4)

        i[0x84] = (self._sty, self._address_zp, 'STY', 'ZP', 2, 3)
        i[0x94] = (self._sty, self._address_zp_x, 'STY', 'ZPX', 2, 4)
        i[0x8C] = (self._sty, self._address_abs, 'STY', 'ABS', 3, 4)

        i[0x38] = (self._sec, self._address_imp, 'SEC', 'IMP', 1, 2)

        i[0xE9] = (self._sbc, self._address_imm, 'SBC', 'IMM', 2, 2)
        i[0xE5] = (self._sbc, self._address_zp, 'SBC', 'ZP', 2, 3)
        i[0xF5] = (self._sbc, self._address_zp_x, 'SBC', 'ZPX', 2, 4)
        i[0xED] = (self._sbc, self._address_abs, 'SBC', 'ABS', 3, 4)
        i[0xFD] = (self._sbc, self._address_abs_x, 'SBC', 'ABX', 3, 4)
        i[0xF9] = (self._sbc, self._address_abs_y, 'SBC', 'ABY', 3, 4)
        i[0xE1] = (self._sbc, self._address_inx, 'SBC', 'INX', 2, 6)
        i[0xF1] = (self._sbc, self._address_iny, 'SBC', 'INY', 2, 5)

        i[0x18] = (self._clc, self._address_imp, 'CLC', 'IMP', 1, 2)

        i[0x60] = (self._rts, self._address_imp, 'RTS', 'IMP', 1, 6)

        i[0x0A] = (self._asl, self._address_imp, 'ASL', 'IMP', 1, 2)
        i[0x06] = (self._asl, self._address_zp, 'ASL', 'ZP', 2, 5)
        i[0x16] = (self._asl, self._address_zp_x, 'ASL', 'ZPX', 2, 6)
        i[0x0E] = (self._asl, self._address_abs, 'ASL', 'ABS', 3, 6)
        i[0x1E] = (self._asl, self._address_abs_x_write, 'ASL', 'ABX', 3, 7)

        i[0x09] = (self._ora, self._address_imm, 'ORA', 'IMM', 2, 2)
        i[0x05] = (self._ora, self._address_zp, 'ORA', 'ZP', 2, 3)
        i[0x15] = (self._ora, self._address_zp_x, 'ORA', 'ZPX', 2, 4)
        i[0x0D] = (self._ora, self._address_abs, 'ORA', 'ABS', 3, 4)
        i[0x1D] = (self._ora, self._address_abs_x, 'ORA', 'ABX', 3, 4)
        i[0x19] = (self._ora, self._address_abs_y, 'ORA', 'ABY', 3, 4)
        i[0x01] = (self._ora, self._address_inx, 'ORA', 'INX', 2, 6)
        i[0x11] = (self._ora, self._address_iny, 'ORA', 'INY', 2, 5)

        i[0x49] = (self._eor, self._address_imm, 'EOR', 'IMM', 2, 2)
        i[0x45] = (self._eor, self._address_zp, 'EOR', 'ZP', 2, 3)
        i[0x55] = (self._eor, self._address_zp_x, 'EOR', 'ZPX', 2, 4)
        i[0x4D] = (self._eor, self._address_abs, 'EOR', 'ABS', 3, 4)
        i[0x5D] = (self._eor, self._address_abs_x, 'EOR', 'ABX', 3, 4)
        i[0x59] = (self._eor, self._address_abs_y, 'EOR', 'ABY', 3, 4)
        i[0x41] = (self._eor, self._address_inx, 'EOR', 'INX', 2, 6)
        i[0x51] = (self._eor, self._address_iny, 'EOR', 'INY', 2, 5)

        i[0xAA] = (self._tax, self._address_imp, 'TAX', 'IMP', 1, 2)

        i[0xC9] = (self._cmp, self._address_imm, 'CMP', 'IMM', 2, 2)
        i[0xC5] = (self._cmp, self._address_zp, 'CMP', 'ZP', 2, 3)
        i[0xD5] = (self._cmp, self._address_zp_x, 'CMP', 'ZPX', 2, 4)
        i[0xCD] = (self._cmp, self._address_abs, 'CMP', 'ABS', 3, 4)
        i[0xDD] = (self._cmp, self._address_abs_x, 'CMP', 'ABX', 3, 4)
        i[0xD9] = (self._cmp, self._address_abs_y, 'CMP', 'ABY', 3, 4)
        i[0xC1] = (self._cmp, self._address_inx, 'CMP', 'INX', 2, 6)
        i[0xD1] = (self._cmp, self._address_iny, 'CMP', 'INY', 2, 5)

        i[0x90] = (self._bcc, self._address_rel, 'BCC', 'REL', 2, 2)

        i[0xCA] = (self._dex, self._address_imp, 'DEX', 'IMP', 1, 2)

        i[0x88] = (self._dey, self._address_imp, 'DEY', 'IMP', 1, 2)

        i[0xC8] = (self._iny, self._address_imp, 'INY', 'IMP', 1, 2)

        i[0xE6] = (self._inc, self._address_zp, 'INC', 'ZP', 2, 5)
        i[0xF6] = (self._inc, self._address_zp_x, 'INC', 'ZPX', 2, 6)
        i[0xEE] = (self._inc, self._address_abs, 'INC', 'ABS', 3, 6)
        i[0xFE] = (self._inc, self._address_abs_x_write, 'INC', 'ABX', 3, 7)

        i[0xC0] = (self._cpy, self._address_imm, 'CPY', 'IMM', 2, 2)
        i[0xC4] = (self._cpy, self._address_zp, 'CPY', 'ZP', 2, 3)
        i[0xCC] = (self._cpy, self._address_abs, 'CPY', 'ABS', 3, 4)

        i[0x48] = (self._pha, self._address_imp, 'PHA', 'IMP', 1, 3)
        i[0x68] = (self._pla, self._address_imp, 'PLA', 'IMP', 1, 4)
        i[0x08] = (self._php, self._address_imp, 'PHP', 'IMP', 1, 3)
        i[0x28] = (self._plp, self._address_imp, 'PLP', 'IMM', 1, 4)

        i[0xC6] = (self._dec, self._address_zp, 'DEC', 'ZP', 2, 5)
        i[0xD6] = (self._dec, self._address_zp_x, 'DEC', 'ZPX', 2, 6)
        i[0xCE] = (self._dec, self._address_abs, 'DEC', 'ABX', 3, 6)
        i[0xDE] = (self._dec, self._address_abs_x_write, 'DEC', 'ABX', 3, 7)

        i[0xA8] = (self._tay, self._address_imp, 'TAY', 'IMP', 1, 2)
        i[0x98] = (self._tya, self._address_imp, 'TYA', 'IMP', 1, 2)

        i[0x4C] = (self._jmp, self._address_abs, 'JMP', 'ABS', 3, 3)
        i[0x6C] = (self._jmp, self._address_ind, 'JMP', 'IND', 3, 5)

        i[0x86] = (self._stx, self._address_zp, 'STX', 'ZP', 2, 3)
        i[0x96] = (self._stx, self._address_zp_y, 'STX', 'ZPY', 2, 4)
        i[0x8E] = (self._stx, self._address_abs, 'STX', 'ABS', 3, 4)

        i[0xEA] = (self._nop, self._address_imp, 'NOP', 'IMP', 1, 2)

        i[0x24] = (self._bit, self._address_zp, 'BIT', 'ZP', 2, 3)
        i[0x2C] = (self._bit, self._address_abs, 'BIT', 'ABS', 3, 4)

        i[0x70] = (self._bvs, self._address_rel, 'BVS', 'REL', 2, 2)
        i[0x50] = (self._bvc, self._address_rel, 'BVC', 'REL', 2, 2)

        i[0xF8] = (self._sed, self._address_imp, 'SED', 'IMP', 1, 2)

        i[0x29] = (self._and, self._address_imm, 'AND', 'IMM', 2, 2)
        i[0x25] = (self._and, self._address_zp, 'AND', 'ZP', 2, 3)
        i[0x35] = (self._and, self._address_zp_x, 'AND', 'ZPX', 2, 4)
        i[0x2D] = (self._and, self._address_abs, 'AND', 'ABS', 3, 4)
        i[0x3D] = (self._and, self._address_abs_x, 'AND', 'ABX', 3, 4)
        i[0x39] = (self._and, self._address_abs_y, 'AND', 'ABY', 3, 4)
        i[0x21] = (self._and, self._address_inx, 'AND', 'INX', 2, 6)
        i[0x31] = (self._and, self._address_iny, 'AND', 'INY', 2, 5)

        i[0xBA] = (self._tsx, self._address_imp, 'TSX', 'IMP', 1, 2)
        
        i[0x00] = (self._brk, self._address_imp, 'BRK', 'IMP', 1, 7)
        i[0x40] = (self._rti, self._address_imp, 'RTI', 'IMP', 1, 6)

        i[0x4A] = (self._lsr, self._address_imp, 'LSR', 'IMP', 1, 2)
        i[0x46] = (self._lsr, self._address_zp, 'LSR', 'ZP', 2, 5)
        i[0x56] = (self._lsr, self._address_zp_x, 'LSR', 'ZPX', 2, 6)
        i[0x4E] = (self._lsr, self._address_abs, 'LSR', 'ABS', 3, 6)
        i[0x5E] = (self._lsr, self._address_abs_x_write, 'LSR', 'ABX', 3, 7)

        i[0x2A] = (self._rol, self._address_imp, 'ROL', 'IMP', 1, 2)
        i[0x26] = (self._rol, self._address_zp, 'ROL', 'ZP', 2, 5)
        i[0x36] = (self._rol, self._address_zp_x, 'ROL', 'ZPX', 2, 6)
        i[0x2E] = (self._rol, self._address_abs, 'ROL', 'ABS', 3, 6)
        i[0x3E] = (self._rol, self._address_abs_x_write, 'ROL', 'ABX', 3, 7)

        i[0x6A] = (self._ror, self._address_imp, 'ROL', 'ABX', 1, 2)
        i[0x66] = (self._ror, self._address_zp, 'ROL', 'ZP', 2, 5)
        i[0x76] = (self._ror, self._address_zp_x, 'ROL', 'ZPX', 2, 6)
        i[0x6E] = (self._ror, self._address_abs, 'ROL', 'ABS', 3, 6)
        i[0x7E] = (self._ror, self._address_abs_x_write, 'ROL', 'ABX', 3, 7)

    def _setup_registers(self):
        """
        初始化寄存器

        Reset interrupts are triggered when the system first starts and when the user presses the
        reset button. When a reset occurs the system jumps to the address located at $FFFC and $FFFD
        """
        self._register_pc = self._read_word(0xFFFC)
        self._register_sp = 0xFD
        self._register_a = 0x00
        self._register_x = 0x00
        self._register_y = 0x00

    def _setup_status_flags(self):
        """
        初始化 CPU 标志位
        """
        self._flag_c = 0
        self._flag_z = 0
        self._flag_i = 0
        self._flag_d = 0
        self._flag_b = 0
        self._flag_v = 0
        self._flag_n = 0

    def _stack_push_byte(self, byte):
        """
        0100 - 01FF 栈空间
        """
        a = self._register_sp + 0x100
        self._write_byte(a, byte)
        self._register_sp = (self._register_sp - 1) & 0xFF

    def _stack_pop_byte(self):
        self._register_sp = (self._register_sp + 1) & 0xFF
        a = self._register_sp + 0x100
        m = self._read_byte(a)
        return m

    def _stack_push_word(self, word):
        low = word & 0xFF
        high = (word >> 8) & 0xFF
        self._stack_push_byte(high)
        self._stack_push_byte(low)

    def _stack_pop_word(self):
        low = self._stack_pop_byte()
        high = self._stack_pop_byte()
        v = (high << 8) + low
        return v

    def _read_byte(self, address):
        m = self._bus.read_byte(address)
        return m

    def _write_byte(self, address, value):
        return self._bus.write_byte(address, value)

    def _read_word(self, address):
        """
        6502 字节顺序是小端
        """
        return self._bus.read_word(address)

    def _write_word(self, address, value):
        return self._bus.write_word(address, value)

    def _shift_right(self, value):
        self._set_carry_flag(bool(value & 0x01))
        result = value >> 1
        self._set_zero_flag(not result)
        self._set_negative_flag(bool(result & 0x80))
        return result

    def _shift_left(self, value):
        self._set_carry_flag(bool(value & 0x80))
        result = (value << 1) & 0xFF
        self._set_zero_flag(not result)
        self._set_negative_flag(bool(result & 0x80))
        return result

    def _rotate_left(self, value):
        result = ((value << 1) & 0xFF) | self._flag_c
        self._set_carry_flag(bool(value & 0x80))
        self._set_zero_flag(not result)
        self._set_negative_flag(bool(result & 0x80))
        return result

    def _rotate_right(self, value):
        result = (value >> 1) | (self._flag_c << 7)
        self._set_carry_flag(bool(value & 0x1))
        self._set_zero_flag(not result)
        self._set_negative_flag(bool(result & 0x80))
        return result

    # TODO 重构 _set_flag_zero _clear_flag_zero
    def _set_carry_flag(self, condition):
        v = 1 if condition else 0
        self._flag_c = v

    def _set_zero_flag(self, condition):
        v = 1 if condition else 0
        self._flag_z = v

    def _set_interrupt_disabled_flag(self, condition):
        v = 1 if condition else 0
        self._flag_i = v

    def _set_decimal_mode_flag(self, condition):
        v = 1 if condition else 0
        self._flag_d = v

    def _set_break_command_flag(self, condition):
        v = 1 if condition else 0
        self._flag_b = v

    def _set_overflow_flag(self, condition):
        v = 1 if condition else 0
        self._flag_v = v

    def _set_negative_flag(self, condition):
        v = 1 if condition else 0
        self._flag_n = v

    """
    寻址模式
    """
    def _address_imp(self):
        self._operand = None

        self._register_pc += 1

    def _address_imm(self):
        self._operand = self._register_pc + 1

        self._register_pc += 2

    def _address_zp(self):
        """
        $0000-$00FF

        :return: 8 bit address operand
        """
        a = self._register_pc + 1
        op = self._read_byte(a) & 0xFF
        self._operand = op

        self._register_pc += 2

    def _address_zp_x(self):
        """
        :return: 8 bit address operand
        """
        a = self._register_pc + 1
        op = (self._read_byte(a) + self._register_x) & 0xFF
        self._operand = op

        self._register_pc += 2

    def _address_zp_y(self):
        """
        :return: 8 bit address operand
        """
        a = self._register_pc + 1
        op = (self._read_byte(a) + self._register_y) & 0xFF
        self._operand = op

        self._register_pc += 2

    def _address_rel(self):
        """
        操作数是 8 位有符号数 -128 ~ 127

        :return: 8 bit signed operand
        """
        a = self._register_pc + 1
        op = byte_to_signed_int(self._read_byte(a))
        self._operand = op

        self._register_pc += 2

    def _address_abs(self):
        a = self._register_pc + 1
        op = self._read_word(a)
        self._operand = op

        self._register_pc += 3

    def _address_abs_x(self):
        """
        :return: 16 bit address
        """
        a = self._register_pc + 1
        a1 = self._read_word(a)
        op = (a1 + self.index_x) & 0xFFFF
        if self._is_new_page(a1, op):
            self._tick()

        self._operand = op

        self._register_pc += 3

    def _address_abs_x_write(self):
        # 写的时候总是增加一个周期
        a = self._register_pc + 1
        a1 = self._read_word(a)
        op = (a1 + self.index_x) & 0xFFFF
        self._tick()
        self._operand = op

        self._register_pc += 3

    def _address_abs_y(self):
        """
        :return: 16 bit address
        """
        a = self._register_pc + 1
        a1 = self._read_word(a)
        op = (a1 + self.index_y) & 0xFFFF
        if self._is_new_page(a1, op):
            self._tick()
        self._operand = op

        self._register_pc += 3

    def _address_abs_y_write(self):
        a = self._register_pc + 1
        a1 = self._read_word(a)
        op = (a1 + self.index_y) & 0xFFFF
        self._tick()
        self._operand = op

        self._register_pc += 3

    # def _address_ind(self):
    #     """
    #     :return: 16 bit address
    #     """
    #     a1 = self._register_pc + 1
    #     a2 = self._read_word(a1)
    #     op = self._read_word(a2) & 0xFFFF
    #     log('a1', hex(a1), 'a2', hex(a2), 'op', hex(op))
    #     self._operand = op
    #
    #     self._register_pc += 3

    def _address_ind(self):
        addr = self._read_word(self._register_pc + 1)
        first_addr = addr
        # There's a bug in the 6502 when fetching the
        # address on a page boundary. It reads
        # the second byte at the beginning of the current page
        # instead of the next one.
        if addr & 0xFF == 0xFF:
            second_addr = addr & 0xFF00
        else:
            second_addr = addr + 1
        self._operand = self._read_byte(first_addr) | (self._read_byte(second_addr) << 8)
        self._register_pc += 3

    def _address_inx(self):
        """
        :return: 16 bit address
        """
        a1 = self._register_pc + 1
        a2 = (self._read_byte(a1) + self.index_x) & 0xFF
        low = self._read_byte(a2)
        high = self._read_byte((a2 + 1) & 0xFF)
        op = (high << 8) + low
        self._operand = op

        self._register_pc += 2

    def _address_iny(self):
        """
        :return: 16 bit address
        """
        a1 = self._read_byte(self._register_pc + 1) & 0xFF
        low = self._read_byte(a1)
        high = self._read_byte((a1 + 1) & 0xFF)
        a2 = (high << 8) + low
        op = (a2 + self.index_y) & 0xFFFF
        if self._is_new_page(a2, op):
            self._tick()
        self._operand = op

        self._register_pc += 2

    def _is_new_page(self, source, target):
        a = (source & 0xFF00)
        b = (target & 0xFF00)
        return a != b

    """
    指令集文档
    http://obelisk.me.uk/6502/reference.html
    """

    def _lda(self):
        m = self._read_byte(self._operand)
        self._register_a = m

        # TODO 重构 set_register_a set_register_x
        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _sta(self):
        self._write_byte(self._operand, self._register_a)

    def _bpl(self):
        if self._flag_n == 0:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _sei(self):
        self._set_interrupt_disabled_flag(True)

    def _cld(self):
        self._set_decimal_mode_flag(False)

    def _cli(self):
        self._set_interrupt_disabled_flag(False)

    def _clv(self):
        self._set_overflow_flag(False)

    def _ldx(self):
        m = self._read_byte(self._operand)
        self._register_x = m

        a = self._register_x
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _txs(self):
        self._register_sp = self._register_x

    def _bne(self):
        if self._flag_z == 0:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _cmp(self):
        a = self._register_a
        m = self._read_byte(self._operand)

        v = a - m
        self._set_carry_flag(v >= 0)
        self._set_zero_flag(v == 0)
        self._set_negative_flag(((v >> 7) & 1) == 1)

    def _txa(self):
        self._register_a = self._register_x

        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _jsr(self):
        # 1 Byte 指令 2 Byte 地址
        # 执行指令时 pc 已经指向下一条指令了
        pc = self._register_pc - 1

        self._stack_push_word(pc)

        self._register_pc = self._operand

    def _jmp(self):
        self._register_pc = self._operand

    def _beq(self):
        if self._flag_z == 1:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _cpx(self):
        a = self._register_x
        m = self._read_byte(self._operand)

        v = (a - m)
        self._set_carry_flag(v >= 0)
        self._set_zero_flag(v == 0)
        self._set_negative_flag(((v >> 7) & 1) == 1)

    def _bcs(self):
        if self._flag_c == 1:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _bmi(self):
        if self._flag_n == 1:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _ldy(self):
        a = self._read_byte(self._operand)
        self._register_y = a

        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _sty(self):
        self._write_byte(self._operand, self._register_y)

    def _sec(self):
        self._set_carry_flag(True)

    def _sbc(self):
        m = self._read_byte(self._operand)
        a = self._register_a
        c = self._flag_c
        v = a + (m ^ 0xFF) + c
        self._set_overflow_flag((a ^ m) & (a ^ v) & 0x80)
        self._set_carry_flag(v & 0x100)
        self._register_a = v & 0xFF

        self._set_zero_flag(self._register_a == 0)
        self._set_negative_flag(self._register_a & 0x80)

    def _adc(self):
        value = self._read_byte(self._operand)
        result = value + self._register_a + self._flag_c
        signed_result = (
                byte_to_signed_int(value) + byte_to_signed_int(self._register_a) + self._flag_c
        )
        self._set_carry_flag(result > 255)
        self._register_a = result & 0xFF
        self._set_zero_flag(not self._register_a)
        self._set_overflow_flag(signed_result < -128 or signed_result > 127)
        self._set_negative_flag(bool(result & 0x80))

    def _clc(self):
        self._set_carry_flag(False)

    def _rts(self):
        self._register_pc = self._stack_pop_word() + 1

    def _asl(self):
        if self._opcode == 0x0A:
            self._register_a = self._shift_left(self._register_a)
        else:
            m = self._read_byte(self._operand)
            v = self._shift_left(m)
            self._write_byte(self._operand, v)

    def _ora(self):
        m = self._read_byte(self._operand)
        self._register_a = m | self._register_a

        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _tax(self):
        self._register_x = self._register_a

        a = self._register_x
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _tay(self):
        self._register_y = self._register_a

        a = self._register_y
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _tya(self):
        self._register_a = self._register_y

        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _bcc(self):
        if self._flag_c == 0:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _dex(self):
        self._register_x = (self._register_x - 1) & 0xFF
        a = self._register_x
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _dey(self):
        self._register_y = (self._register_y - 1) & 0xFF
        a = self._register_y
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _iny(self):
        self._register_y = (self._register_y + 1) & 0xFF
        a = self._register_y
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _inx(self):
        self._register_x = (self._register_x + 1) & 0xFF
        a = self._register_x
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _inc(self):
        m = (self._read_byte(self._operand) + 1) & 0xFF
        self._write_byte(self._operand, m)
        a = m
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _dec(self):
        m = (self._read_byte(self._operand) - 1) & 0xFF
        self._write_byte(self._operand, m)
        a = m
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _cpy(self):
        m = self._read_byte(self._operand)
        y = self._register_y
        a = y - m
        self._set_carry_flag(a >= 0)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(((a >> 7) & 1) == 1)

    def _pha(self):
        self._stack_push_byte(self._register_a)

    def _pla(self):
        self._register_a = self._stack_pop_byte()

        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _php(self):
        self._stack_push_byte(self.status | 0b00010000)

    def _plp(self):
        value = self._stack_pop_byte()

        self._set_carry_flag(bool(value & 0x1))
        self._set_zero_flag(bool(value & 0x2))
        self._set_interrupt_disabled_flag(bool(value & 0x4))
        self._set_decimal_mode_flag(bool(value & 0x8))
        self._set_overflow_flag(bool(value & 0x40))
        self._set_negative_flag(bool(value & 0x80))

    def _stx(self):
        self._write_byte(self._operand, self._register_x)

    def _nop(self):
        pass

    def _bit(self):
        v = self._read_byte(self._operand)
        self._set_overflow_flag(bool(v & 0b01000000))
        self._set_negative_flag(bool(v & 0b10000000))
        self._set_zero_flag(not (self._register_a & v))

    def _bvs(self):
        if self._flag_v == 1:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _bvc(self):
        if self._flag_v == 0:
            self._tick()

            target = self._register_pc + self._operand
            if self._is_new_page(self._register_pc, target):
                self._tick()

            self._register_pc = target

    def _sed(self):
        self._set_decimal_mode_flag(True)

    def _and(self):
        m = self._read_byte(self._operand)
        self._register_a = self._register_a & m
        self._set_zero_flag(not self._register_a)
        self._set_negative_flag(bool(self._register_a & 0x80))

    def _eor(self):
        value = self._read_byte(self._operand)
        self._register_a = self._register_a ^ value
        self._set_zero_flag(not self._register_a)
        self._set_negative_flag(bool(self._register_a & 0x80))

    def _tsx(self):
        self._register_x = self._register_sp

        a = self._register_x
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _lsr(self):
        if self._opcode == 0x4A:
            self._register_a = self._shift_right(self._register_a)
        else:
            m = self._read_byte(self._operand)
            v = self._shift_right(m)
            self._write_byte(self._operand, v)

    def _rol(self):
        if self._opcode == 0x2A:
            self._register_a = self._rotate_left(self._register_a)
        else:
            m = self._read_byte(self._operand)
            v = self._rotate_left(m)
            self._write_byte(self._operand, v)

    def _ror(self):
        if self._opcode == 0x6A:
            self._register_a = self._rotate_right(self._register_a)
        else:
            m = self._read_byte(self._operand)
            v = self._rotate_right(m)
            self._write_byte(self._operand, v)

    def _brk(self):
        """
        IRQ interrupt vector at $FFFE/F
        """
        if self._flag_i == 1:
            return
        self._stack_push_word(self._register_pc)
        self._stack_push_byte(self.status | 0b00010000)

        self._set_break_command_flag(True)
        self._register_pc = self._read_word(0xFFFE)

    def _rti(self):
        value = self._stack_pop_byte()
        self._set_carry_flag(bool(value & 0x1))
        self._set_zero_flag(bool(value & 0x2))
        self._set_interrupt_disabled_flag(bool(value & 0x4))
        self._set_decimal_mode_flag(bool(value & 0x8))
        self._set_overflow_flag(bool(value & 0x40))
        self._set_negative_flag(bool(value & 0x80))

        self._register_pc = self._stack_pop_word()

    def reset(self):
        self._setup_status_flags()
        self._setup_registers()

        self._cycles = 0
        self.tick(8)

    def tick(self, cycles):
        self._cycles += cycles
        self._bus.sync(cycles)

    def connect_to_bus(self, bus):
        self._bus = bus
        self._setup_registers()

    def _decode_opcode(self):
        self._current_instruction = self._instruction_set[self._opcode]
        execute, fetch_operand, name, mode, i_bytes, cycles = self._current_instruction
        self._cycles_costs = cycles
        self._fetch_operand = fetch_operand
        self._execute = execute

    def _execute_instruction(self):
        self._fetch_operand()
        self._execute()

    def emulate_once(self):
        self._opcode_from_memory()
        self._decode_opcode()
        # if self.debug:
        #     self.debug_nestest()
        # log(self._current_instruction[-4])
        self._execute_instruction()
        self._update_clock_cycles(self._cycles_costs)
        # 同步 ppu
        self._bus.sync(self._cycles)
        self._cycles = 0

    def _tick(self):
        self._cycles += 1

    def _update_clock_cycles(self, cycles):
        self._cycles += cycles

    def handle_nmi(self):
        self._stack_push_word(self._register_pc)
        self._stack_push_byte(self.status | 0b00010000)
        self._set_interrupt_disabled_flag(True)
        self._register_pc = self._read_word(0xFFFA)
        self._bus.sync(2)

    def debug_nestest(self):
        # ppu_ctrl_1 = self._ppu.control_1
        # ppu_ctrl_2 = self._ppu.control_2
        # ppu_status = self._read_byte(0x2002)
        # spr_ram_address = self._read_byte(0x2003)
        # spr_ram_io = self._read_byte(0x2004)
        # vram_address = self._read_word(0x2005)
        # vram_io = self._read_byte(0x2007)
        """
        Writes cause a DMA transfer to occur from CPU memory at
        address $100 x n, where n is the value written, to SPR-RAM. 
        """
        spr_dma = self._read_byte(0x4014)
        *others, cycles = self._instruction_set[self._opcode]
        s = self._cycles
        i = self._count
        self._count += 1
        output2 = [
            self._register_pc,
            self._opcode,
            self._register_a,
            self._register_x,
            self._register_y,
            self.status,
            self._register_sp,
            # ppu_ctrl_1,
            # ppu_ctrl_2,
            # s,
        ]
        expect2 = log_list[i]
        cycles = expect2[-1]
        expect2.pop()
        expect2.pop()
        expect2.pop()
        # expect2.append(cycles)
        # log('ppu', [
        #     ppu_ctrl_1,
        #     ppu_ctrl_2,
        #     ppu_status,
        #     spr_ram_address,
        #     spr_ram_io,
        #     vram_address,
        #     vram_io,
        # ])
        if expect2 != output2:
            log('<{}>'.format(i))
            log([hex(o) for o in output2])
            log([hex(o) for o in expect2])
            assert False

    def _opcode_from_memory(self):
        self._opcode = self._read_byte(self._register_pc)

    def run(self):
        while True:
            try:
                self.emulate_once()
            except Exception as e:
                log('ERROR count {}'.format(self._count-1), hex(self._opcode).upper(), self._current_instruction[3], e)
                break
