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
            "ST"  : 5,
            "BEQ"   : 4,
            "BNE"   : 4,
            "BLT"   : 4,
            "BGT"   : 4,
            "J"     : 4,
            "B"     : 4,
            "HALT"  : 0}

        
    def rename(self, cpu, instr_type, operands):
        """renames logical registers operands to physical register operands"""
        renamed_operands = []

        for i, operand in enumerate(operands):
            if operand[0] == "R": # if logical register used just do a look up instead else must be immediate so keep the same
                if instr_type in { "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"} or i > 0:
                    operand = cpu.rat.check(operand)
                else:
                    operand = cpu.rat.add(operand)
            renamed_operands.append(operand)

        return renamed_operands

    def resolve_branch_labels(self, operands):
        """make operands machine readable [decode branch labels into numbers]"""
        resolved_operands = []
        for operand in operands:
            if operand in self.branch_label_decode: 
                resolved_operands.append(self.branch_label_decode[operand][0])
            else: # handels immediate and register operands 
                resolved_operands.append(operand)
        return resolved_operands

    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        end_msg = False
     
        for _ in range(cpu.super_scaling):
            instr_type, operands, index = None, None, None

            # find available instructiont to decode
            for idx, item in enumerate(cpu.INSTR_BUFF):
                if type(item) != Instruction:
                    instr_type, operands = item
                    index = idx
                    break
            
            # ran out of instructions to decode but cycles still going so flag to print empty deocde msg at bottom
            if not instr_type:
                end_msg = True
                break
        
            resolved_operands = self.resolve_branch_labels(operands)
            renamed_operands = self.rename(instr_type=instr_type, operands=resolved_operands, cpu=cpu)

            # create instruction
            operands = np.asarray(renamed_operands) # convert to numpy array
            instruction = Instruction(type=instr_type, operands=operands, cycle_latency=self.latencies[instr_type]) # create instruction object
            cpu.INSTR_BUFF[index] = instruction # replace instruction with decoded instruction
            print(f"Decoded: {instruction}")

        if end_msg:
            print("Decoded: []")

        return True



