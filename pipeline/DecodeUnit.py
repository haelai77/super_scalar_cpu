from .Instruction import Instruction
import numpy as np

class DecodeUnit:
    # in future handles reservation stations and which execution unit to use
    # should for now just call the execution unit with appropriate instruction

    def __init__(self) -> None:
        pass

    def decode(self, cpu):
        ''' decodes operands, stores operands into registers (will eventually be done by the LSU)'''
        instr, operands = cpu.INSTR_BUFF[0]
        resolved_operands = []

        for operand in operands: # converts string reg operand into index in RF file
            if operand[0] == "R":
                resolved_operands.append(int(operand[1])) # e.g. R1:str -> 1: int (not decoded into value in register because need to tell writeback address)
            else:
                resolved_operands.append(int(operand)) 

        resolved_operands = np.asarray(resolved_operands) # convert to numpy array
        instruction = Instruction(type=instr, operands=resolved_operands) # create instruction object

        cpu.INSTR_BUFF[0] = instruction # replace instruction with decoded instruction

        # match instr:
        #     case "ADD" | "SUB" | "MUL" | "DIV" | "CMP" | "BEQ" | "BNE" | "BLT" | "BGT": # replace operands with values in registers
        #         regAddr1 = operands[1][1]
        #         regAddr2 = operands[2][1]
        #         val1 = self.cpu.RF.read(regAddr1)
        #         val2 = self.cpu.RF.read(regAddr2)

        #         operands = [val1, val2] # sets registers to their values in instruction buffer

        #     case "ADDI":
        #         regAddr = int((operands[1][1])) # gets value from string e.g. in "R0" = 0
        #         operands[0] = self.cpu.RF.read(regAddr)

        #     case "LDI": # load constant/immediate into register
        #         immediate = operands[1]
        #         regAddr = int(operands[0][1])

        #         self.cpu.RF.write(regAddr, immediate)

        #     case "LD": # load from memory into register
        #         mem_val = self.cpu.memory[operands[1]]
        #         regAddr = int(operands[0][1])

        #         self.cpu.RF.write(regAddr, mem_val)

        #     case "J": # jump pc to address in register
        #          regAddr = int(operands[0][1])
        #          operands = self.cpu.RF.read(regAddr2)



