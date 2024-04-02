from collections import deque
import pandas as pd


class LSU:
    def __init__(self, ID) -> None:
        self.RS_type = "LSU"
        self.AVAILABLE = True
        self.instr = None # pd.Series, will be instruction type after execution
        self.cycle_latency = 0
        self.ID = ID

        self.exe = {
            "LD"    : self.LD, # address resolution
            "LDI"   : self.LDI,
            "ST"    : self.ST, # address resolution
        }

    def take_instruction(self, cpu):
        self.instr = cpu.RS[self.RS_type].pop(cpu)
        if type(self.instr) == pd.Series:
            self.AVAILABLE = False
            return True
        else:
            return False
    
    def execute(self, cpu):
       
        
        # wait for latency to be over
        # (decoding step sets up the latency)
        if self.cycle_latency > 1:
            self.cycle_latency -= 1
            print(f"Executing (lsu_{self.ID}): latency {self.cycle_latency}, {self.instr["INSTRs"]}")
            return False
        print(f"Executed (lsu_{self.ID}): {self.instr["INSTRs"]}")
        
        # execute instruction
        instr_type = self.instr["INSTRs"].type
        instruction = self.exe[instr_type](cpu)

        cpu.CDB.append(instruction)
        self.AVAILABLE = True
        
        # only need to broadcast if writing to destination
        if instruction.type != "ST":

            # broadcast results to reservation stations
            for rs_type in ["ALU", "LSU"]: # todo include branch BRANCH
                cpu.RS[rs_type].broadcast(rob_entry=cpu.PRF.rob_entry(instruction.operands[0]), result=instruction.result)

            # broad cast results to possible awaiting stores
            cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0]) # operand zero is dst reg
        
        self.instr = None
        return True
    
    def LD(self, cpu): 
        '''r1 <- MEM[regs[r2] + regs[r3]]'''
        # at this point it should have result either already filled via ST in rob or not filled and just need to read
        if not self.instr["INSTRs"].result:
            self.instr["INSTRs"].result = cpu.MEM.read(f"MEM{int(self.instr["val1"]) + int(self.instr["val2"])}")
        instruction = self.instr["INSTRs"]
      
        return instruction

    def LDI(self, cpu):
        ''' takes immediate and stores it into register specified in instruction
        - r1 <- immediate'''
        instruction = self.instr["INSTRs"]
        instruction.result = self.instr["immediate"]
        return instruction

    def ST(self, cpu):
        '''memory[regs[r2] + regs[r3]] <- rf[r1] # only done by rob if speculative'''
        instruction = self.instr["INSTRs"]

        # if there is a value able to be written back assign prep for CDB
        if self.instr["val1"]:
            instruction.result = self.instr["val1"]

        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction
