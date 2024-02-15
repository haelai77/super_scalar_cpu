from .Instruction import Instruction
from collections import deque
from typing import Deque
from .LSU import LSU

class ExecuteUnit:
    def __init__(self) -> None:
        self.RS: Deque[tuple] = deque(maxlen = 8)
        self.LSU = LSU()

        self.exe = {
            "ADD"   : self.ADD,
            "ADDI"  : self.ADD, # after decoding adding is the same as regs are replaced with values
            
            "SUB"   : self.SUB,

            "MUL"   : self.MUL,
            "DIV"   : self.DIV,

            "CMP"   : self.CMP,

            "LD"    : self.LSU.LD,
            "LDI"   : self.LSU.LDI,
            "ST"    : self.LSU.ST,

            "BEQ"   : self.BEQ,
            "BNE"   : self.BNE,
            "BLT"   : self.BLT,
            "BGT"   : self.BGT,

            "J"     : self.J,
            "B"     : self.B,

            "HALT"  : self.HALT
        }

    def execute(self, cpu):
        instruction: Instruction = cpu.INSTR_BUFF[0]
        instr_type = instruction.type
        self.exe[instr_type](instr=instruction, cpu=cpu)

        # print(f"instr: {instr_type} \n REGS3: {cpu.RF.rf[:4]} \n pc: {cpu.PC}")

    def ADD(self, instr, cpu):
        '''add 2 registers and store in 3rd reg (also handels ADDI)'''
        instr.result = cpu.RF.read(instr.operands[1]) + cpu.RF.read(instr.operands[2]) # calculate result

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

    def BEQ(self, instr, cpu):
        # in MIPS +4 to pc as to move to next 32bit/4byte instruction, then you add branch displacement 
        # in this simulator the program counter is incremented by branch displacement then 1 is added back in the cpu object
        '''relative branching if values in 2 registers are equal'''
        if cpu.RF.read(instr.operands[0]) == cpu.RF.read(instr.operands[1]):
            cpu.PC += (instr.operands[2])
        
    def BNE(self, instr, cpu):
        '''relative relative branching if values in 2 registers are not equal'''
        if cpu.RF.read(instr.operands[0]) != cpu.RF.read(instr.operands[1]):
            cpu.PC += (instr.operands[2])
    
    def BLT(self, instr, cpu):
        '''relative branch if value in first register is less than '''
        if cpu.RF.read(instr.operands[0]) < cpu.RF.read(instr.operands[1]):
            cpu.PC += (instr.operands[2])

    def BGT(self, instr, cpu):
        '''relative branch if value in first register is greater than '''
        if cpu.RF.read(instr.operands[0]) > cpu.RF.read(instr.operands[1]):
            cpu.PC += (instr.operands[2])

    def J(self, instr, cpu):
        '''relative branch based on immediate passed in '''
        cpu.PC += (instr.operands[0])

    def B(self, instr, cpu):
        '''direct branch to address provided'''
        cpu.PC = instr.operands[0]

    def HALT(self, instr, cpu):
        '''stop!'''
        cpu.finished = True
