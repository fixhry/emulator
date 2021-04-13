from utils import *


class CPU:
    """
    寄存器
        PC 16-bit
        SP 8-bit
            The stack is located at memory locations $0100-$01FF
        Accumulator (A) 8-bit
        Index Register X (X) 8-bit
        Index Register Y (Y) 8-bit
        Processor Status (P)
            7 6 5 4 3 2 1 0
            N V   B D I Z C
            Carry Flag (C)
                The carry flag is set if the last instruction resulted in an overflow from bit 7 or an underflow from bit 0
            Zero Flag (Z)
                The zero flag is set if the result of the last instruction was zero
            Interrupt Disable (I)
                The interrupt disable flag can be used to prevent the system responding to IRQs
            Decimal Mode (D)
                The decimal mode flag is used to switch the 6502 into BCD mode
            Break Command (B)
                The break command flag is used to indicate that a BRK (Break) instruction has been executed, causing an IRQ
            Overflow Flag (V)
                The overflow flag is set if an invalid two’s complement result was obtained by the previous instruction
            Negative Flag (N)
                Bit 7 of a byte represents the sign of that byte, with 0 being positive and 1 being negative

    中断
        The addresses to jump to when an interrupt occurs are stored in a vector table in
        the program code at $FFFA-$FFFF. When an interrupt occurs the system performs the
        following actions:

        56 种指令 151 valid opcodes

    """

    def __init__(self, memory):
        self._setup_registers()
        self._setup_status_flags()
        self.memory = memory

    @property
    def program_counter(self):
        return self._program_counter

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @property
    def accumulator(self):
        return self._accumulator

    @property
    def index_x(self):
        return self._index_x

    @property
    def index_y(self):
        return self._index_y

    @property
    def status(self):
        v = ((self._carry_flag << 0) +
             (self._zero_flag << 1) +
             (self._interrupt_disabled_flag << 2) +
             (self._decimal_mode_flag << 3) +
             (self._break_command_flag << 4) +
             (1 << 5) +
             (self._overflow_flag << 6) +
             (self._negative_flag << 7))
        return v

    def _setup_registers(self):
        """
        初始化寄存器
        """
        self._program_counter = 0xC000
        self._stack_pointer = 0x00
        self._accumulator = 0x00
        self._index_x = 0x00
        self._index_y = 0xFD

    def _setup_status_flags(self):
        """
        初始化 CPU 标志位
        """
        self._carry_flag = 1
        self._zero_flag = 0
        self._interrupt_disabled_flag = 1
        self._decimal_mode_flag = 1
        self._break_command_flag = 1
        self._overflow_flag = 1
        self._negative_flag = 1

    def _read_byte(self, address):
        return self.memory.read_byte(address)

    def _read_word(self, address):
        """
        6502 字节顺序是小端
        """
        return self.memory.read_word(address)

    """
    寻址模式
    """

    def _addressing_immediate(self):
        """
        :return: 8 bit constant
        """
        a = self._program_counter + 1
        op = self._read_byte(a) & 0xFF
        return op

    def _addressing_zero_page(self):
        """
        $0000-$00FF

        :return: 8 bit address operand
        """
        a = self._program_counter + 1
        op = self._read_byte(a) & 0xFF
        return op

    def _addressing_zero_page_x(self):
        """
        :return: 8 bit address operand
        """
        a = self._program_counter + 1
        op = (self._read_byte(a) + self._index_x) & 0xFF
        return op

    def _addressing_zero_page_y(self):
        """
        :return: 8 bit address operand
        """
        a = self._program_counter + 1
        op = (self._read_byte(a) + self._index_y) & 0xFF
        return op

    def _addressing_relative(self):
        """
        操作数是 8 位有符号数 -128 ~ 127

        :return: 8 bit signed operand
        """
        a = self._program_counter + 1
        op = byte_to_signed_int(self._read_byte(a))
        return op

    def _addressing_absolute(self):
        """
        :return: 16 bit address
        """
        a = self._program_counter + 1
        op = self._read_word(a) & 0xFFFF
        return op

    def _addressing_absolute_x(self):
        """
        :return: 16 bit address
        """
        a = self._program_counter + 1
        op = (self._read_word(a) + self.index_x) & 0xFFFF
        return op

    def _addressing_absolute_y(self):
        """
        :return: 16 bit address
        """
        a = self._program_counter + 1
        op = (self._read_word(a) + self.index_y) & 0xFFFF
        return op

    def _addressing_indirect(self):
        """
        :return: 16 bit address
        """
        a1 = self._program_counter + 1
        a2 = self.read_word(a1)
        op = self._read_word(a2) & 0xFFFF
        return op

    def _addressing_indexed_indirect(self):
        """
        :return: 16 bit address
        """
        a1 = self._program_counter + 1
        a2 = self._read_byte(a1) + self.index_x
        op = self._read_word(a2) & 0xFFFF
        return op

    def _addressing_indirect_indexed(self):
        """
        :return: 16 bit address
        """
        a1 = self._program_counter + 1
        a2 = self._read_byte(a1)
        op = (self._read_word(a2) + self.index_y) & 0xFFFF
        return op

    """
    指令类型
    • Load / Store Operations - Load a register from memory or stores the contents of a
    register to memory.
    
    • Register Transfer Operations - Copy contents of X or Y register to the accumulator or
    copy contents of accumulator to X or Y register.
    
    • Stack Operations - Push or pull the stack or manipulate stack pointer using X register.
    
    
    
    • Increments / Decrements - Increment or decrement the X or Y registers or a value stored
    in memory.
    
    • Shifts - Shift the bits of either the accumulator or a memory location one bit to the left or
    right.
     
    • Jumps / Calls - Break sequential execution sequence, resuming from a specified address.
    
    • Status Register Operations - Set or clear a flag in the status register.
    
    • System Functions - Perform rarely used functions. 
    """

    """
        Arithmetic Operations - Perform arithmetic operations on registers and memory.
    """

    def _adc(self):
        """
            Add with Carry
        """
        pass

    def _asl(self):
        """
            Arithmetic Shift Left
        """
        pass

    """
        Logical Operations - Perform logical operations on the accumulator and a value stored in memory.
    """

    def _and(self):
        """
            Logical AND
        """
        pass

    """
        Branches - Break sequential execution sequence, resuming from a specified address, if a
        condition is met. The condition involves examining a specific bit in the status register.
    """

    def _bcc(self):
        """
            Branch if Carry Clear
        """
        pass

    def _bcs(self):
        """
            Branch if Carry Set
        """
        pass

    def _beq(self):
        """
            Branch if Equal
        """
        pass

    def _bit(self):
        """
            Bit Test
        """
        pass

