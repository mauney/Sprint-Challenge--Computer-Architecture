"""CPU functionality."""

import sys

# Instructions
ADD = 0b10100000  # 0
# AND  = 0b10101000  # 8
CALL = 0b01010000  # 0
# CMP  = 0b10100111  # 7
DEC  = 0b01100110  # 6
# DIV  = 0b10100011  # 3
HLT = 0b00000001  # 1
INC  = 0b01100101  # 5
INT  = 0b01010010  # 2
IRET = 0b00010011  # 3
JEQ  = 0b01010101  # 5
JGE  = 0b01011010  # 10
JGT  = 0b01010111  # 7
JLE  = 0b01011001  # 9
JLT  = 0b01011000  # 8
JMP = 0b01010100  # 4
JNE  = 0b01010110  # 6
# LD   = 0b10000011  # 3
LDI = 0b10000010  # 2
# MOD  = 0b10100100  # 4
MUL = 0b10100010  # 2
# NOP  = 0b00000000  # 0
# NOT  = 0b01101001  # 9
# OR   = 0b10101010  # 10
POP = 0b01000110  # 6
# PRA  = 0b01001000  # 8
PRN = 0b01000111  # 7
PUSH = 0b01000101  # 5
RET = 0b00010001  # 1
# SHL  = 0b10101100  # 12
# SHR  = 0b10101101  # 13
ST = 0b10000100  # 4
# SUB  = 0b10100001  # 1
# XOR  = 0b10101011  # 11

# Other constants
IM = 5
IS = 6
SP = 7  # the stack pointer is stored in the register at index 7


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # ir represents the Instruction Register
        self.ir = None
        # pc represents the Program Counter register
        self.pc = 0
        # fl represents the Flag Status register
        self.fl = 0
        # reg represents the eight general purpose registers
        self.reg = [0] * 8
        # initialize the stack pointer
        self.reg[SP] = 0xF4
        # ram represents 256 bytes of random access memory
        self.ram = [0] * 256
        # interrupt flag
        self.interrupts_enabled = True
        # operands
        self.operand_a = None
        self.operand_b = None
        self.num_operands = None
        # branch table
        self.branchtable = {
            ADD:  self.add,
            DEC:  self.dec,
            CALL: self.call,
            HLT:  self.hlt,
            INC:  self.inc,
            INT:  self.intr,
            IRET: self.iret,
            JMP:  self.jmp,
            LDI:  self.ldi,
            MUL:  self.mul,
            POP:  self.pop,
            PRN:  self.prn,
            PUSH: self.push,
            RET:  self.ret,
            ST:   self.st,
            }

    # Utility methods

    def ram_read(self, MAR):
        return self.ram[MAR]

    def ram_write(self, MDR, MAR):
        self.ram[MAR] = MDR

    def set_operands(self):
        self.num_operands = self.ir >> 6
        if self.num_operands == 1:
            self.operand_a = self.ram_read(self.pc + 1)
        elif self.num_operands == 2:
            self.operand_a = self.ram_read(self.pc + 1)
            self.operand_b = self.ram_read(self.pc + 2)

    def invoke_instruction(self):
        if self.ir in self.branchtable:
            self.branchtable[self.ir]()
        else:
            print(f"I did not understand that ir: {self.ir:b}")
            sys.exit(1)

    def move_pc(self):
        # grab the fifth digit of the ir
        instruction_sets_pc = ((self.ir << 3) & 255) >> 7
        if not instruction_sets_pc:
            self.pc += (self.num_operands + 1)

    def check_interrupts(self):
        masked_interrupts = self.reg[IM] & self.reg[IS]
        for i in range(8):
            interrupt_happened = ((masked_interrupts >> i) & 1) == 1
            if interrupt_happened:
                # pause interrupt checking
                self.interrupts_enabled = False
                # reset interrupt
                self.reg[IS] = self.reg[IS] & (255 - 2**i)
                # push values to the stack
                self.reg[SP] -= 1
                self.ram[self.reg[SP]] = self.reg[self.pc]
                self.reg[SP] -= 1
                self.ram[self.reg[SP]] = self.reg[self.fl]
                for j in range(7):
                    self.reg[SP] -= 1
                    self.ram[self.reg[SP]] = self.reg[j]
                # set the pc
                self.pc = self.ram[0xF8 + i]

    # Instruction methods

    def add(self):
        self.alu('ADD', self.operand_a, self.operand_b)

    def call(self):
        # push pc + 2 onto the stack
        self.reg[SP] -= 1
        self.ram[self.reg[SP]] = self.pc + 2
        # jump to value stored in register
        self.jmp()

    def dec(self):
        self.alu('DEC', self.operand_a)

    def hlt(self):
        sys.exit(0)

    def inc(self):
        self.alu('INC', self.operand_a)

    def intr(self):
        interrupt = self.reg[self.operand_a]
        self.reg[IS] = self.reg[IS] | 2**(i)

    def iret(self):
        for i in range(6, -1, -1):
            self.reg[i] = self.ram[self.reg[SP]]
            self.reg[SP] += 1
        self.fl = self.ram[self.reg[SP]]
        self.reg[SP] += 1
        self.pc = self.ram[self.reg[SP]]
        self.reg[SP] += 1
        self.interrupts_enabled = True

    def jmp(self):
        # set pc to value stored in register
        self.pc = self.reg[self.operand_a]

    def ldi(self):
        self.reg[self.operand_a] = self.operand_b

    def mul(self):
        self.alu('MUL', self.operand_a, self.operand_b)

    def pop(self):
        if self.reg[SP] > 0xF3:
            print('Error: the stack is empty')
            sys.exit(3)
        else:
            self.reg[self.operand_a] = self.ram[self.reg[SP]]
            self.reg[SP] += 1

    def prn(self):
        print(self.reg[self.operand_a])

    def push(self):
        # move to the next position in the stack
        self.reg[SP] -= 1
        # assign the value
        self.ram[self.reg[SP]] = self.reg[self.operand_a]

    def ret(self):
        self.pc = self.ram[self.reg[SP]]

    def st(self):
        # Store value in regB location to ram location indicated by regA value
        self.ram_write(self.reg[self.operand_b], self.reg[self.operand_a])

    def alu(self, op, reg_a, reg_b=None):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "DEC":
            self.reg[reg_a] -= 1
        elif op == "INC":
            self.reg[reg_a] += 1
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        # elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")
        # Some alu operations may set a value outside of our LS8's 8-bit range
        # Mask any potentially changed value with OxFF to enforce 8-bit limit
        self.reg[reg_a] = self.reg[reg_a] & 0xFF

    # Debug method

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    # External methods

    def load(self, program):
        """Load a program into memory."""

        address = 0

        try:
            with open(program, 'r') as f:
                for line in f:
                    # strip out comment, if any, and whitespace
                    instruction = line.split('#')[0].strip()
                    if instruction == '':
                        continue
                    self.ram[address] = int(instruction, base=2)
                    address += 1

        except FileNotFoundError:
            print(f'File not found. path: {program}')
            sys.exit(2)

    def run(self):
        """Run the CPU."""
        import time
        interrupt_time = time.time() + 60
        # set to True to run interrupts.ls8
        timer = True
        while True:
            if timer:
                if time.time() > interrupt_time:
                    # Set bit 0 of the IS register (R6)
                    self.reg[6] = self.reg[6] | 0b00000001
                    interrupt_time = time.time() + 60
            if self.interrupts_enabled:
                self.check_interrupts()
            self.ir = self.ram_read(self.pc)
            self.set_operands()
            self.invoke_instruction()
            self.move_pc()
