from .Instruction import Instruction
import numpy as np

class DecodeUnit:
    # in future handles reservation stations and which execution unit to use
    # should for now just call the execution unit with appropriate instruction

    def __init__(self, branch_label_map) -> None:
        self.branch_label_decode = branch_label_map
        self.latencies = {
            "ADD"   : 4,
            "ADDI"  : 4,
            "SUB"   : 4,
            "MUL"   : 4,
            "DIV"   : 13,
            "CMP"   : 4,
            "LD"  : 5,
            "LDI" : 5,
            "ST"  : 4,
            "BEQ"   : 4,
            "BNE"   : 4,
            "BLT"   : 4,
            "BGT"   : 4,
            "J"     : 4,
            "B"     : 4,
            "HALT"  : 0}

    def issue(self, cpu):
        '''assign instruction to execution unit if possible'''
        counter = 0
        instrs = []
        for execution_unit in cpu.execute_units:
            if execution_unit.AVAILABLE and counter < cpu.super_scaling:
                execution_unit.instr = next(instr for instr in cpu.INSTR_BUFF if type(instr) == Instruction)
                execution_unit.cycle_latency = execution_unit.instr.cycle_latency
                counter += 1

                instrs.append(execution_unit.instr)

        if counter < cpu.super_scaling:
            print("Issuing: blocked/waiting")
        else:
            print(f"Issuing: {instrs}")

        return not counter < cpu.super_scaling

    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        instr, operands, index = None, None, None

        for idx, item in enumerate(cpu.INSTR_BUFF):
            if type(item) != Instruction:
                instr, operands = item
                index = idx
        
        if instr == None:
            return

        resolved_operands = []
        for operand in operands: 
            # pops off any "R"s and converts to int
            if operand[0] in {"R", "r"} and len(operand) == 2:
                resolved_operands.append(int(operand[1])) # e.g. R1:str -> 1: int (not decoded into value in register because need to tell writeback address)
            
            # for B instruction decoding labels into index in instruction cache
            elif operand in self.branch_label_decode: 
                resolved_operands.append(self.branch_label_decode[operand][0])

            else:
                resolved_operands.append(int(operand)) 

        resolved_operands = np.asarray(resolved_operands) # convert to numpy array
        instruction = Instruction(type=instr, operands=resolved_operands, cycle_latency=self.latencies[instr]) # create instruction object

        cpu.INSTR_BUFF[index] = instruction # replace instruction with decoded instruction




