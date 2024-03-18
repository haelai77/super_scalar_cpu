from .Instruction import Instruction
from collections import deque
from typing import Deque
from .LSU import LSU


class ExecuteUnit:
    def __init__(self) -> None:
        self.RS: Deque[tuple] = deque(maxlen = 8)
        self.LSU = LSU()
        self.AVAILABLE = True
        self.instr: Instruction = None 
        self.cycle_latency = 0

        self.exe = {
            "ADD"   : self.ADD,
            "ADDI"  : self.ADDI, # after decoding adding is the same as regs are replaced with values
            
            "SUB"   : self.SUB,

            "MUL"   : self.MUL,
            "DIV"   : self.DIV,

            "CMP"   : self.CMP,

            "LD"    : self.LD, # address resolution
            "LDI"   : self.LSU.LDI,
            "ST"    : self.ST, # address resolution

            "BEQ"   : self.BEQ,
            "BNE"   : self.BNE,
            "BLT"   : self.BLT,
            "BGT"   : self.BGT,

            "J"     : self.J,
            "B"     : self.B,

            "HALT"  : self.HALT
        }

    def execute(self, cpu):
        # issuing step sets up the latency
        self.AVAILABLE = False

        if self.cycle_latency > 0:
            self.cycle_latency -= 1
            return
        else:
            print(f"Executing: latency {self.cycle_latency}")
            pass
        
        print(f"Executing: {self.instr}")
        instr_type = self.instr.type
        self.exe[instr_type](instr=self.instr, cpu=cpu)
        self.instr.done = True
        self.instr = None

        self.AVAILABLE = True

    def ADD(self, instr, cpu):
        '''add 2 registers and store in 3rd reg (also handels ADDI)'''
        instr.result = cpu.RF.read(instr.operands[1]) + cpu.RF.read(instr.operands[2]) # calculate result

    def ADDI(self, instr, cpu):
        instr.result = cpu.RF.read(instr.operands[1]) + instr.operands[2]

    def SUB(self, instr, cpu):
        '''sub 2 registers and store in 3rd reg'''
        instr.result = cpu.RF.read(instr.operands[1]) - cpu.RF.read(instr.operands[2]) # calculate result

    def MUL(self, instr, cpu):
        '''mul 2 registers and store in 3rd reg'''
        instr.result = cpu.RF.read(instr.operands[1]) * cpu.RF.read(instr.operands[2]) # calculate result

    def DIV(self, instr, cpu):
        '''integer div 2 registers and store in 3rd reg'''
        instr.result = cpu.RF.read(instr.operands[1]) // cpu.RF.read(instr.operands[2]) # calculate result
    
    def CMP(self, instr, cpu):
        '''compare the values in 2 registers and store result in third
            1. r1 < r2 = -1
            2. r1 > r2 = 1
            3. r1 == r2 = -0'''
        if cpu.RF.read(instr.operands[1]) < cpu.RF.read(instr.operands[2]):
            result = -1
        elif cpu.RF.read(instr.operands[1]) > cpu.RF.read(instr.operands[1]):
            result = 1
        else:
            result = 0
        
        instr.result = result

    def LD(self, instr, cpu):
        '''r1 <- mem[regs[r2] + regs[r3]] ARGS: r1, offset_reg, bp_reg'''
        # address resolution and then call LSU
        offset = cpu.RF.read(instr.operands[1])
        bp = cpu.RF.read(instr.operands[2])
        instr.operands[1] = offset+bp
        self.LSU.LD(instr, cpu)
    
    def ST(self, instr, cpu):
        '''mem[regs[r2] + regs[r3]] <- r1'''
        offset = cpu.RF.read(instr.operands[1])
        bp = cpu.RF.read(instr.operands[2])
        instr.operands[1] = offset+bp
        self.LSU.ST(instr, cpu)

    def BEQ(self, instr, cpu):
        # in MIPS +4 to pc as to move to next 32bit/4byte instruction, then you add branch displacement 
        # in this simulator the program counter is incremented by branch displacement then 1 is added back in the cpu object
        '''branching if values in 2 registers are equal'''
        if cpu.RF.read(instr.operands[0]) == cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])
        
    def BNE(self, instr, cpu):
        '''branching if values in 2 registers are not equal'''
        if cpu.RF.read(instr.operands[0]) != cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])
    
    def BLT(self, instr, cpu):
        '''branch if value in first register is less than '''
        if cpu.RF.read(instr.operands[0]) < cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])

    def BGT(self, instr, cpu):
        '''branch if value in first register is greater than '''
        if cpu.RF.read(instr.operands[0]) > cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])

    def J(self, instr, cpu):
        ''' branch based on immediate passed in '''
        cpu.PC += (instr.operands[0])

    def B(self, instr, cpu):
        '''direct branch to address provided'''
        cpu.PC = instr.operands[0]

    def HALT(self, instr, cpu):
        '''stop!'''
        cpu.finished = True
