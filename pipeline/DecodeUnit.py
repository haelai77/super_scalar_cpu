from .Instruction import Instruction
import numpy as np

class DecodeUnit:
    # in future handles reservation stations and which execution unit to use
    # should for now just call the execution unit with appropriate instruction

    def __init__(self, branch_label_map) -> None:
        self.branch_label_decode = branch_label_map

    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        instr, operands = cpu.INSTR_BUFF[0]
        resolved_operands = []

        # print(f"decode: {instr} {operands}")

        for operand in operands: # pops off any "R"s and converts to int
            if operand[0] in {"R", "r"} and len(operand) == 2:
                resolved_operands.append(int(operand[1])) # e.g. R1:str -> 1: int (not decoded into value in register because need to tell writeback address)
            elif operand in self.branch_label_decode: # for B instruction decoding labels into index in instruction cache
                resolved_operands.append(self.branch_label_decode[operand][0])
            else:
                resolved_operands.append(int(operand)) 

        resolved_operands = np.asarray(resolved_operands) # convert to numpy array
        instruction = Instruction(type=instr, operands=resolved_operands) # create instruction object

        cpu.INSTR_BUFF[0] = instruction # replace instruction with decoded instruction




