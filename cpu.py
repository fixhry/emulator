import json


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
    o = o[:-1]
    msg = """
        -------- {} -----------
        -------- output -------
        {}
        -------- expected ------
        {}
    """.format(index, o, expected)
    for i, s in enumerate(o):
        e = expected[i]
        # INY 不检查
        # if s != "INY":
        assert e == s, msg


class CPU:
    """
    中断
        The addresses to jump to when an interrupt occurs are stored in a vector table in
        the program code at $FFFA-$FFFF. When an interrupt occurs the system performs the
        following actions:
    """

    def __init__(self, memory):
        self._memory = memory
        self._setup_instruction_set()
        self._setup_registers()
        self._setup_status_flags()

        # 操作数
        self._opcode = None
        self._operand = None
        # TODO CPU 周期

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
        i = [()] * 256
        i[0xA9] = (self._lda, self._address_imm, 'LDA', 'IMM')
        i[0xAD] = (self._lda, self._address_abs, 'LDA', 'ABS')
        i[0xBD] = (self._lda, self._address_abs_x, 'LDA', 'ABX')
        i[0xA5] = (self._lda, self._address_zp, 'LDA', 'ZP')
        i[0xB5] = (self._lda, self._address_zp_x, 'LDA', 'ZPX')
        i[0xB1] = (self._lda, self._address_iny, 'LDA', 'INY')
        i[0xA1] = (self._lda, self._address_inx, 'LDA', 'INX')
        i[0xB9] = (self._lda, self._address_abs_y, 'LDA', 'ABY')

        i[0x10] = (self._bpl, self._address_rel, 'BPL', 'REL')
        i[0x78] = (self._sei, self._address_imp, 'SEI', 'IMP')
        i[0xD8] = (self._cld, self._address_imp, 'CLD', 'IMP')
        i[0x58] = (self._cli, self._address_imp, 'CLI', 'IMP')
        i[0xB8] = (self._clv, self._address_imp, 'CLV', 'IMP')

        i[0xA2] = (self._ldx, self._address_imm, 'LDX', 'IMM')
        i[0xA6] = (self._ldx, self._address_zp, 'LDX', 'ZP')
        i[0xB6] = (self._ldx, self._address_zp_y, 'LDX', 'ZPY')
        i[0xAE] = (self._ldx, self._address_abs, 'LDX', 'ABS')
        i[0xBE] = (self._ldx, self._address_abs_y, 'LDX', 'ABY')

        i[0x9A] = (self._txs, self._address_imp, 'TXS', 'IMP')

        i[0x8D] = (self._sta, self._address_abs, 'STA', 'ABS')
        i[0x95] = (self._sta, self._address_zp_x, 'STA', 'ZPX')
        i[0x9D] = (self._sta, self._address_abs_x, 'STA', 'ABX')
        i[0x85] = (self._sta, self._address_zp, 'STA', 'ZP')
        i[0x81] = (self._sta, self._address_inx, 'STA', 'INX')
        i[0x91] = (self._sta, self._address_iny, 'STA', 'INY')
        i[0x99] = (self._sta, self._address_abs_y, 'STA', 'ABY')

        i[0xE8] = (self._inx, self._address_imp, 'INX', 'IMP')
        i[0xD0] = (self._bne, self._address_rel, 'BNE', 'REL')
        i[0x8A] = (self._txa, self._address_imp, 'TXA', 'IMP')
        i[0x20] = (self._jsr, self._address_abs, 'JSR', 'ABS')
        i[0xF0] = (self._beq, self._address_rel, 'BEQ', 'REL')

        i[0xE0] = (self._cpx, self._address_imm, 'CPX', 'IMM')
        i[0xE4] = (self._cpx, self._address_zp, 'CPX', 'ZP')
        i[0xEC] = (self._cpx, self._address_abs, 'CPX', 'ABS')

        i[0xB0] = (self._bcs, self._address_rel, 'BCS', 'REL')
        i[0x30] = (self._bmi, self._address_rel, 'BMI', 'REL')

        i[0xA0] = (self._ldy, self._address_imm, 'LDY', 'IMM')
        i[0xA4] = (self._ldy, self._address_zp, 'LDY', 'ZP')
        i[0xB4] = (self._ldy, self._address_zp_x, 'LDY', 'ZPX')
        i[0xAC] = (self._ldy, self._address_abs, 'LDY', 'ABS')
        i[0xBC] = (self._ldy, self._address_abs_x, 'LDY', 'ABX')

        i[0x84] = (self._sty, self._address_zp, 'STY', 'ZP')
        i[0x94] = (self._sty, self._address_zp_x, 'STY', 'ZPX')
        i[0x8C] = (self._sty, self._address_abs, 'STY', 'ABS')

        i[0x38] = (self._sec, self._address_imp, 'SEC', 'IMP')

        i[0xE9] = (self._sbc, self._address_imm, 'SBC', 'IMM')
        i[0xE5] = (self._sbc, self._address_zp, 'SBC', 'ZP')
        i[0xF5] = (self._sbc, self._address_zp_x, 'SBC', 'ZPX')
        i[0xED] = (self._sbc, self._address_abs, 'SBC', 'ABS')
        i[0xFD] = (self._sbc, self._address_abs_x, 'SBC', 'ABX')
        i[0xF9] = (self._sbc, self._address_abs_y, 'SBC', 'ABY')
        i[0xE1] = (self._sbc, self._address_inx, 'SBC', 'INX')
        i[0xF1] = (self._sbc, self._address_iny, 'SBC', 'INY')

        i[0x18] = (self._clc, self._address_imp, 'CLC', 'IMP')

        i[0x69] = (self._adc, self._address_imm, 'ADC', 'IMM')
        i[0x65] = (self._adc, self._address_zp, 'ADC', 'ZP')
        i[0x75] = (self._adc, self._address_zp_x, 'ADC', 'ZPX')
        i[0x6D] = (self._adc, self._address_abs, 'ADC', 'ABS')
        i[0x7D] = (self._adc, self._address_abs_x, 'ADC', 'ABX')
        i[0x79] = (self._adc, self._address_abs_y, 'ADC', 'ABY')
        i[0x61] = (self._adc, self._address_inx, 'ADC', 'INX')
        i[0x71] = (self._adc, self._address_iny, 'ADC', 'INY')

        i[0x60] = (self._rts, self._address_imp, 'RTS', 'IMP')

        i[0x0A] = (self._asl, self._address_imp, 'ASL', 'IMP')
        i[0x06] = (self._asl, self._address_zp, 'ASL', 'ZP')
        i[0x16] = (self._asl, self._address_zp_x, 'ASL', 'ZPX')
        i[0x0E] = (self._asl, self._address_abs, 'ASL', 'ABS')
        i[0x1E] = (self._asl, self._address_abs_x, 'ASL', 'ABX')

        i[0x09] = (self._ora, self._address_imm, 'ORA', 'IMM')
        i[0x05] = (self._ora, self._address_zp, 'ORA', 'ZP')
        i[0x15] = (self._ora, self._address_zp_x, 'ORA', 'ZPX')
        i[0x0D] = (self._ora, self._address_abs, 'ORA', 'ABS')
        i[0x1D] = (self._ora, self._address_abs_x, 'ORA', 'ABX')
        i[0x19] = (self._ora, self._address_abs_y, 'ORA', 'ABY')
        i[0x01] = (self._ora, self._address_inx, 'ORA', 'INX')
        i[0x11] = (self._ora, self._address_iny, 'ORA', 'INY')

        i[0x49] = (self._eor, self._address_imm, 'EOR', 'IMM')

        i[0xAA] = (self._tax, self._address_imp, 'TAX', 'IMP')

        i[0xC9] = (self._cmp, self._address_imm, 'CMP', 'IMM')
        i[0xC5] = (self._cmp, self._address_zp, 'CMP', 'ZP')
        i[0xD5] = (self._cmp, self._address_zp_x, 'CMP', 'ZPX')
        i[0xCD] = (self._cmp, self._address_abs, 'CMP', 'ABS')
        i[0xDD] = (self._cmp, self._address_abs_x, 'CMP', 'ABX')
        i[0xD9] = (self._cmp, self._address_abs_y, 'CMP', 'ABY')
        i[0xC1] = (self._cmp, self._address_inx, 'CMP', 'INX')
        i[0xD1] = (self._cmp, self._address_iny, 'CMP', 'INY')

        i[0x90] = (self._bcc, self._address_rel, 'BCC', 'REL')

        i[0xCA] = (self._dex, self._address_imp, 'DEX', 'IMP')

        i[0x88] = (self._dey, self._address_imp, 'DEY', 'IMP')

        i[0xC8] = (self._iny, self._address_imp, 'INY', 'IMP')

        i[0xE6] = (self._inc, self._address_zp, 'INC', 'ZP')
        i[0xF6] = (self._inc, self._address_zp_x, 'INC', 'ZPX')
        i[0xEE] = (self._inc, self._address_abs, 'INC', 'ABS')
        i[0xFE] = (self._inc, self._address_abs_x, 'INC', 'ABX')

        i[0xC0] = (self._cpy, self._address_imm, 'CPY', 'IMM')
        i[0xC4] = (self._cpy, self._address_zp, 'CPY', 'ZP')
        i[0xCC] = (self._cpy, self._address_abs, 'CPY', 'ABS')

        i[0x48] = (self._pha, self._address_imp, 'PHA', 'IMP')
        i[0x68] = (self._pla, self._address_imp, 'PLA', 'IMP')
        i[0x08] = (self._php, self._address_imp, 'PHP', 'IMP')
        i[0x28] = (self._plp, self._address_imp, 'PLP', 'IMM')

        i[0xC6] = (self._dec, self._address_zp, 'DEC', 'ZP')
        i[0xD6] = (self._dec, self._address_zp_x, 'DEC', 'ZPX')
        i[0xCE] = (self._dec, self._address_abs, 'DEC', 'ABX')
        i[0xDE] = (self._dec, self._address_abs_x, 'DEC', 'ABX')

        i[0xA8] = (self._tay, self._address_imp, 'TAY', 'IMP')
        i[0x98] = (self._tya, self._address_imp, 'TYA', 'IMP')

        i[0x4C] = (self._jmp, self._address_abs, 'JMP', 'ABS')
        i[0x6C] = (self._jmp, self._address_ind, 'JMP', 'IND')

        i[0x86] = (self._stx, self._address_zp, 'STX', 'ZP')
        i[0x96] = (self._stx, self._address_zp_y, 'STX', 'ZPY')
        i[0x8E] = (self._stx, self._address_abs, 'STX', 'ABS')

        i[0xEA] = (self._nop, self._address_imp, 'NOP', 'IMP')

        i[0x24] = (self._bit, self._address_zp, 'BIT', 'ZP')
        i[0x2C] = (self._bit, self._address_abs, 'BIT', 'ABS')

        i[0x70] = (self._bvs, self._address_rel, 'BVS', 'REL')
        i[0x50] = (self._bvc, self._address_rel, 'BVC', 'REL')

        i[0xF8] = (self._sed, self._address_imp, 'SED', 'IMP')

        i[0x29] = (self._and, self._address_imm, 'AND', 'IMM')
        i[0x31] = (self._and, self._address_iny, 'AND', 'INY')

        i[0xBA] = (self._tsx, self._address_imp, 'TSX', 'IMP')
        
        i[0x00] = (self._brk, self._address_imp, 'BRK', 'IMP')
        i[0x40] = (self._rti, self._address_imp, 'RTI', 'IMP')

        i[0x4A] = (self._lsr, self._address_imp, 'LSR', 'IMP')
        i[0x46] = (self._lsr, self._address_zp, 'LSR', 'ZP')
        i[0x56] = (self._lsr, self._address_zp_x, 'LSR', 'ZPX')
        i[0x4E] = (self._lsr, self._address_abs, 'LSR', 'ABS')
        i[0x5E] = (self._lsr, self._address_abs_x, 'LSR', 'ABX')

        i[0x2A] = (self._rol, self._address_imp, 'ROL', 'IMP')
        i[0x26] = (self._rol, self._address_zp, 'ROL', 'ZP')
        i[0x36] = (self._rol, self._address_zp_x, 'ROL', 'ZPX')
        i[0x2E] = (self._rol, self._address_abs, 'ROL', 'ABS')
        i[0x3E] = (self._rol, self._address_abs_x, 'ROL', 'ABX')

        i[0x6A] = (self._ror, self._address_abs_x, 'ROL', 'ABX')
        i[0x66] = (self._ror, self._address_zp, 'ROL', 'ZP')
        i[0x76] = (self._ror, self._address_zp_x, 'ROL', 'ZPX')
        i[0x6E] = (self._ror, self._address_abs, 'ROL', 'ABS')
        i[0x7E] = (self._ror, self._address_abs_x, 'ROL', 'ABX')

        self._instruction_set = i
        # self._instruction_set = [
        #     # 操作 寻址模式 指令名 寻址模式 CPU 周期
        #     (self._lda, self._address_imm, 'LDA', 'IMM', 7)
        # ]

    def _setup_registers(self):
        """
        初始化寄存器

        Reset interrupts are triggered when the system first starts and when the user presses the
        reset button. When a reset occurs the system jumps to the address located at $FFFC and $FFFD
        """
        # self._register_pc = self._read_word(0xFFFC)
        self._register_pc = 0xC000

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
        self._flag_i = 1
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
        self._register_sp -= 1

    def _stack_pop_byte(self):
        self._register_sp += 1
        a = self._register_sp + 0x100
        m = self._read_byte(a)
        return m

    def _stack_push_word(self, word):
        low = word & 0xFF
        high = (word >> 8) & 0xFF
        self._stack_push_byte(low)
        self._stack_push_byte(high)

    def _stack_pop_word(self):
        high = self._stack_pop_byte()
        low = self._stack_pop_byte()
        v = (high << 8) + low
        return v

    def _read_byte(self, address):
        m = self._memory.read_byte(address) & 0xFF
        return m

    def _write_byte(self, address, value):
        return self._memory.write_byte(address, value)

    def _read_word(self, address):
        """
        6502 字节顺序是小端
        """
        return self._memory.read_word(address)

    def _write_word(self, address, value):
        return self._memory.write_word(address, value)

    def _shift_right(self, value):
        self._flag_c = bool(value & 0x80)
        result = (value << 1) & 0xFF
        self._flag_z = not result
        self._flag_n = bool(result & 0x80)
        return result

    def _rotate_left(self, value):
        result = ((value << 1) & 0xFF) | int(self._flag_c)
        self._flag_c = bool(value & 0x80)
        self._flag_z = not result
        self._flag_n = bool(result & 0x80)
        return result

    def _rotate_right(self, value):
        result = (value >> 1) | (int(self._flag_c) << 7)
        self._flag_c = bool(value & 0x1)
        self._flag_z = not result
        self._flag_n = bool(result & 0x80)
        return result

    # TODO 重命名 _set_flag_zero _clear_flag_zero
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
    # TODO 把 pc 的自增提取出去
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
        op = (self._read_word(a) + self.index_x) & 0xFFFF
        self._operand = op
        self._register_pc += 3

    def _address_abs_y(self):
        """
        :return: 16 bit address
        """
        a = self._register_pc + 1
        op = (self._read_word(a) + self.index_y) & 0xFFFF
        self._operand = op
        self._register_pc += 3

    def _address_ind(self):
        """
        :return: 16 bit address
        """
        a1 = self._register_pc + 1
        a2 = self.read_word(a1)
        op = self._read_word(a2) & 0xFFFF
        self._operand = op
        self._register_pc += 3

    def _address_inx(self):
        """
        :return: 16 bit address
        """
        a1 = self._register_pc + 1
        a2 = self._read_byte(a1) + self.index_x
        op = self._read_word(a2) & 0xFFFF
        self._operand = op
        self._register_pc += 2

    def _address_iny(self):
        """
        :return: 16 bit address
        """
        a1 = self._register_pc + 1
        a2 = self._read_byte(a1)
        op = (self._read_word(a2) + self.index_y) & 0xFFFF
        self._operand = op
        self._register_pc += 2

    """
    指令集文档
    http://obelisk.me.uk/6502/reference.html
    """

    def _lda(self):
        m = self._read_byte(self._operand)
        self._register_a = m

        a = self._register_a
        # log('lda', hex(self._operand), hex(m))
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

    def _sta(self):
        self._write_byte(self._operand, self._register_a)

    def _bpl(self):
        if self._flag_n == 0:
            # +1 if branch succeeds
            pc = (self._register_pc + self._operand) & 0xFFFF
            self._register_pc = pc

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
            self._register_pc = (self._operand + self._register_pc) & 0xFFFF

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
        pc = self._register_pc

        self._stack_push_word(pc)

        self._register_pc = self._operand

    def _jmp(self):
        self._register_pc = self._operand

    def _beq(self):
        if self._flag_z == 1:
            self._register_pc = (self._register_pc + self._operand) &0xFFFF

    def _cpx(self):
        a = self._register_x
        m = self._read_byte(self._operand)

        v = (a - m)
        self._set_carry_flag(v >= 0)
        self._set_zero_flag(v == 0)
        self._set_negative_flag(((v >> 7) & 1) == 1)

    def _bcs(self):
        if self._flag_c == 1:
            self._register_pc += self._operand

    def _bmi(self):
        if self._flag_n == 1:
            self._register_pc += self._operand

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
        high = self._stack_pop_byte()
        low = self._stack_pop_byte()
        pc = (high << 8) + low
        self._register_pc = pc

    def _asl(self):
        if self._opcode == 0x0A:
            self._set_carry_flag((self._register_a >> 7) == 1)
            self._register_a = (self._register_a << 1)

        a = self._register_a
        bit7 = (a >> 7)
        self._set_zero_flag(a == 0)
        self._set_negative_flag(bit7 == 1)

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
            self._register_pc += self._operand

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
            self._register_pc += self._operand

    def _bvc(self):
        if self._flag_v == 0:
            self._register_pc += self._operand

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
        self._stack_push_word(self._register_pc)
        self._stack_push_byte(self.status | 0b00010000)

        self._set_break_command_flag(True)
        self._register_pc = self._read_word(0xFFFE)

    def _rti(self):
        value = self._stack_pop_byte()
        self._set_carry_flag(bool(value & 0x1))
        self._set_zero_flag(bool(value & 0x2))
        self._set_interrupt_disabled_flag(False)
        self._set_decimal_mode_flag(bool(value & 0x8))
        self._set_overflow_flag(bool(value & 0x40))
        self._set_negative_flag(bool(value & 0x80))

        self._register_pc = self._stack_pop_word()

    def _unknown_opcode(self, opcode):
        s1 = hex(opcode)
        s2 = hex(self._register_pc - 1)
        msg = "不支持的指令 {}, {}".format(s1, s2)
        raise NotImplementedError(msg)

    def debug_nestest(self, count, pc):
        output2 = [
            pc,
            self._opcode,
            self._register_a,
            self._register_x,
            self._register_y,
            self.status,
            self._register_sp,
        ]
        expect2 = log_list[count]
        if expect2 != output2:
            log('<{}>'.format(count))
            log([hex(o) for o in output2])
            log([hex(o) for o in expect2])
            assert False

    def _opcode_from_memory(self):
        self._opcode = self._read_byte(self._register_pc)

    def run(self):
        """
        TODO 目前逻辑上还不太通顺的点
        1. pc 的自增应该在当前指令执行完成后，取下一条指令前单独用一个函数执行?
        2. 执行指令的逻辑有点奇怪
        """

        count = 0
        while True:
            try:
                self._opcode_from_memory()
                op = hex(self._opcode)
                i = self._instruction_set[self._opcode]
                # log('ins', i)
                # log(count)
                execute_instruction, fetch_operand, name, *other = self._instruction_set[self._opcode]
                pc = self._register_pc

                fetch_operand()
                self.debug_nestest(count, pc)
                execute_instruction()
                count += 1
            except Exception as e:
                log('ERROR {}'.format(count), hex(self._opcode).upper(), e)
                # m180 = hex(self._memory.d[0x180:0x200])
                m180 = self._memory.d[0x17e:0x182]
                log('180', m180)
                m17f = hex(self._memory.d[0x17f])
                log('17f', m17f)
                break

