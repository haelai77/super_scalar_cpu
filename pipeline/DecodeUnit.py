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
            "HALT"  : 0}

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

    # def branch_prediction(self, cpu, curr_instr):
    #             # if branch instruction check BTB
    #     if curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}:
            
    #         if cpu.dynamic:
    #             to_take = cpu.BTB.take(cpu.PC)
                
    #             # static prediction
    #             if to_take == "not_in_BTB":
    #                 taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
    #                 cpu.BTB.add(pc=cpu.PC, target= int(curr_instr[1][2]), taken_state=taken_state)

    #                 if taken_state:
    #                     cpu.RSB.append(cpu.PC + 1) # buffer rollback to not taken state
    #                     cpu.PC = int(curr_instr[1][2]) # 2nd operand i.e. target
    #                 else:
    #                     cpu.RSB.append(int(curr_instr[1][2]) + 1) # roll back to taken state

    #             # dynamic prediction
    #             elif to_take >= 0:
    #                 cpu.RSB.append(cpu.PC+1) # buffer rollback to not taken state
    #                 cpu.PC = int(to_take)
    #             else:
    #                 cpu.RSB.append(int(curr_instr[1][2])+1)

    #         # static prediction
    #         else:
    #             taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
    #             # if taken, buffer rollback to not taken path
    #             if taken_state:
    #                 cpu.RSB.append(cpu.PC+1)
    #                 cpu.PC = int(curr_instr[1][2]) # 3rd operand i.e. target
    #             else:
    #                 print("buffering not taken ",int(curr_instr[1][2]), cpu.PC+1)
    #                 cpu.RSB.append(int(curr_instr[1][2])+1)

    #     elif curr_instr[0] == "J":
    #         cpu.PC += int(curr_instr[1][0])
    #     elif curr_instr[0] == "B":
    #         cpu.PC = int(curr_instr[1][0])

    def decode(self, cpu):
        ''' decodes operands in to objects which contain'''
        end_msg = False

        for _ in range(cpu.super_scaling):
            instr_type, operands, index, pc = None, None, None, None

            # find available instructiont to decode
            for idx, instr in enumerate(cpu.INSTR_BUFF):
                if type(instr) != Instruction: 
                    instr_type, operands, pc = instr
                    index = idx
                    break
            
            # ran out of instructions to decode but cycles still going so flag to print empty deocde msg at bottom
            if not instr_type:
                end_msg = True
                break

            renamed_operands = self.rename(instr_type=instr_type, operands=operands, cpu=cpu)

            if renamed_operands is False:
                print(" >>>No free physical registers stalling<<<")
                return

            # create instruction
            renamed_operands = np.asarray(renamed_operands) # convert to numpy array
            instruction = Instruction(type=instr_type, operands=renamed_operands, cycle_latency=self.latencies[instr_type]) # create instruction object
            instruction.pc = pc
            instruction.logical_operands = operands
            cpu.INSTR_BUFF[index] = instruction # replace instruction with decoded instruction
            print(f"Decoded: {instruction}")

        if end_msg:
            print("Decoded: []")

        return True



