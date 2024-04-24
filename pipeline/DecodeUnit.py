from .Instruction import Instruction
import numpy as np
import copy

class DecodeUnit:
    def __init__(self) -> None:
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
            "HALT"  : 0,
            "NOP"   : 5,}

    def rename(self, cpu, instr_type, operands):
        """renames logical registers operands to physical register operands"""
        if len(operands) > len(cpu.rat.freelist):
            return False

        renamed_operands = [None] * len(operands)

        for i in range(len(operands)-1, -1, -1):
            operand = operands[i]
            #note if you have e.g. add R1 R1 R2 this may cause issues as you want the old mapping for R1 therefore we iterate in reverse to read mappings followed by renaming the result register
            if operand[0] == "R": # if logical register used just do a look up instead else must be immediate so keep the same
                if instr_type in { "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"} or i > 0:
                    operand = cpu.rat.check(operand)
                else:
                    operand = cpu.rat.add(operand)
            renamed_operands[i] = operand

        return renamed_operands

    # def static_prediction(self, style, target, cpu):
    #     match style:
    #         case "FIXED_always":
    #             return 1
    #         case "FIXED_never":
    #             return 0
    #         case "STATIC":
    #             return target < cpu.PC# always take backwards jump
    #     return False

    # def branch_prediction(self, cpu, curr_instr):
    #             # if branch instruction check BTB
    #     if curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}:
    #         instr_pc = curr_instr[2]

    #         if cpu.dynamic:
    #             to_take = cpu.BTB.take(instr_pc)
                
    #             # static prediction
    #             if to_take == "not_in_BTB":
    #                 taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
    #                 cpu.BTB.add(pc=instr_pc, target=int(curr_instr[1][2]), taken_state=taken_state)

    #                 if taken_state:
    #                     print("  >>x predict taken <<")
    #                     cpu.RSB.append(instr_pc + 1) # buffer rollback to not taken state
    #                     cpu.PC = int(curr_instr[1][2]) # 2nd operand i.e. target
    #                 else:
    #                     print("  >>x predict not taken <<")
    #                     cpu.RSB.append(int(curr_instr[1][2]) + 1) # roll back to taken state

    #             # dynamic prediction
    #             elif to_take >= 0:
    #                 print("  >> predict taken <<")
    #                 cpu.RSB.append(instr_pc + 1) # buffer rollback to not taken state
    #                 cpu.PC = int(to_take)
    #             else:
    #                 print("  >> predict not taken <<")
    #                 cpu.RSB.append(int(curr_instr[1][2])+1)

    #         # static prediction
    #         else:
    #             taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
    #             # if taken, buffer rollback to not taken path
    #             if taken_state:
    #                 cpu.RSB.append(instr_pc+1)
    #                 cpu.PC = int(curr_instr[1][2]) # 3rd operand i.e. target
    #             else:
    #                 print("buffering not taken ",int(curr_instr[1][2]), instr_pc+1)
    #                 cpu.RSB.append(int(curr_instr[1][2])+1)


    
    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        if len(cpu.IQ) == cpu.IQ.maxlen:
                print("Decode: [] >> IQ full")
                return False

        # for _ in range(cpu.super_scaling):

        instr_type, operands, pc = None, None, None

        # if cpu.super_scaling > 1 and pc == cpu.PC:# pretty sure I don't need the greater than 1 # NOTE as for super scaling we do a section of the pipeline twice we don't want to issue early for an earlier fetch in cycle
        #     print("Decoded: []") # for super scaling 
        #     return False

        # find available instructiont to decode
        for instr in (cpu.INSTR_BUFF):
            if type(instr) != Instruction:
                instr_type, operands, pc = instr
                # if pc == cpu.PC: # skip instructions that were fetched in the same cycle
                #     continue
                break

        #     print("Decode: [] >> can't decode something fetched in the same cycle")
        #     return False

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

        renamed_operands = self.rename(instr_type=instr_type, operands=operands, cpu=cpu)

        if renamed_operands is False:
            print(" >>>No free physical registers stalling<<<")
            return False

        # create instruction
        renamed_operands = np.asarray(renamed_operands) # convert to numpy array
        instruction = Instruction(type=instr_type, operands=renamed_operands, cycle_latency=self.latencies[instr_type]) # create instruction object
        instruction.pc = pc
        instruction.logical_operands = operands

        cpu.INSTR_BUFF.popleft()
        cpu.IQ.append(instruction) # replace instruction with decoded instruction
        
        print(f"Decoded: {instruction}")

        # cpu.PC += 1

            # break # 1 decode per decode call
        return True



