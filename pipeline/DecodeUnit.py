from .Instruction import Instruction
import numpy as np
import copy

class DecodeUnit:
    def __init__(self) -> None:
        self.latencies = {
            "ADD"   : 2,
            "ADDI"  : 2,
            "SUB"   : 2,
            "MUL"   : 2,
            "DIV"   : 7,
            "CMP"   : 2,

            "LD"  : 3,
            "LDI" : 3,
            "ST"  : 3,
            "STI"  : 3,

            "STPI": 3, #
            "LDPI": 3, #

            "VLD" : 3,
            "VST" : 3,

            "VLDS" : 3,
            "VSTS" : 3,

            "VADD"  : 3,
            "VMUL"  : 3,
            "VSUB"  : 3,
            "VDIV"  : 8,
            "VDOT"  : 3,

            "BEQ"   : 2,
            "BNE"   : 2,
            "BLT"   : 2,
            "BGT"   : 2,
            "J"     : 2,
            "B"     : 2,
            "HALT"  : 0,
            "NOP"   : 5,}

    def rename(self, cpu, instr_type, operands):
        """renames logical registers operands to physical register operands"""
        if instr_type == "LDPI" and len(operands)-1 > len(cpu.rat.freelist):
            return False, False
        elif len(operands)-1 > len(cpu.rat.freelist):
            return False, False
        
        base_reg = None
        renamed_operands = [None] * len(operands)

        for i in range(len(operands)-1, -1, -1):
            operand = operands[i]
            #note if you have e.g. add R1 R1 R2 this may cause issues as you want the old mapping for R1 therefore we iterate in reverse to read mappings followed by renaming the result register
            if operand[0] == "R": # if logical register used just do a look up instead else must be immediate so keep the same
                
                ############### for indexed instructions
                if instr_type in {"STPI", "LDPI"} and i == 2: # we want to read the last operand but add to rat for the first 2
                    operand = cpu.rat.check(operand)
                    
                elif instr_type in {"STPI", "LDPI"} and i == 1:
                    logical_reg = operand
                    operand = cpu.rat.check(operand) # for reading R2 with old physical register
                    base_reg = cpu.rat.add(logical_reg) # for writing R2 with new physical register
                    
                ###############
                elif instr_type in { "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "STPI"} or i > 0:
                    operand = cpu.rat.check(operand)
                else:
                    operand = cpu.rat.add(operand)
            elif operand == "VLR":
                operand = cpu.rat.add(operand)

            renamed_operands[i] = operand
        return renamed_operands, base_reg
    
    def v_rename(self, cpu, instr_type, operands):
        # we only need to rename if VST or VLD
        if len(operands)-2 > len(cpu.rat.v_freelist):
            return False, False
        
        word_len = operands[0]
        operands = operands[1:]
        if instr_type =="VSTS" and len(operands) != 3:
            raise Exception("missing operand")
        renamed_operands = [None] * (len(operands)+(instr_type in {"VST", "VSTS", "VLD", "VLDS"})) # +1 because operands present + extra VLR operand + 1

        # iterate backwards through operands
        for i in range(len(operands)-1, -1, -1):
            if (instr_type in {"VST", "VSTS"} and i == 0) or i > 0:
                renamed_operands[i] = cpu.rat.check(operands[i])
            else:
                renamed_operands[i] = cpu.rat.add(operands[i])

        if instr_type in {"VST", "VLD", "VSTS", "VLDS"}:
            renamed_operands[-1] = cpu.rat.check("VLR")
            if renamed_operands[-1] is None:
                raise Exception("vector length not set before vector instruction")
        return (renamed_operands, word_len)

    
    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        if len(cpu.IQ) == cpu.IQ.maxlen:
                print("Decode: [] >> IQ full")
                return False

        # for _ in range(cpu.super_scaling):

        instr_type, operands, pc = None, None, None

        # find available instructiont to decode
        for instr in (cpu.INSTR_BUFF):
            if type(instr) != Instruction:
                instr_type, operands, pc = instr
                break


        # ran out of instructions to decode but cycles still going so flag to print empty deocde msg at bottom
        if instr_type is None:
            print(f"Decoded: []")
            return True
        
        # if cpu.bra_pred and instr_type in {"BEQ", "BNE", "BLT", "BGT"}:
        #     self.branch_prediction(cpu=cpu, curr_instr=(instr_type, operands, pc)) #NOTE: does branch prediction
        # elif instr_type == "J":
        #     cpu.PC += int(operands[0])
        # elif instr_type == "B":
        #     cpu.PC = int(operands[0])
        bin_word_size = None
        base_reg = None
        if instr_type not in {"VST", "VLD", "VADD", "VSUB", "VDIV", "VMUL", "VSTS", "VLDS", "VDOT"}:
            renamed_operands, base_reg = self.rename(instr_type=instr_type, operands=operands, cpu=cpu)
        else:
            renamed_operands, bin_word_size = self.v_rename(cpu=cpu, instr_type=instr_type, operands=operands)


        if renamed_operands is False:
            print(" >>>No free physical registers stalling<<<")
            return False

        # create instruction
        renamed_operands = np.asarray(renamed_operands) # convert to numpy array
        instruction = Instruction(type=instr_type, operands=renamed_operands, cycle_latency=self.latencies[instr_type]) # create instruction object
        instruction.pc = pc
        instruction.logical_operands = operands if instr_type[0] != "V" else operands[1:] # if vector skip first operand as it isn't actually an operand but a int bit word size

        if base_reg is not None:
            instruction.base_reg = base_reg
        
        if bin_word_size is not None:
            instruction.bitpack_size = int(bin_word_size)
        

        cpu.INSTR_BUFF.popleft()
        cpu.IQ.append(instruction) # replace instruction with decoded instruction
        
        print(f"Decoded: {instruction}")

        # cpu.PC += 1

            # break # 1 decode per decode call
        return True



