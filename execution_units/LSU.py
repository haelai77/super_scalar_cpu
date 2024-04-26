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
            "STPI"  : self.STPI,
            "LDPI"  : self.LDPI,
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

        ###################
        # broadcast results to reservation stations 
        if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:
            
            for rs_type in ["ALU", "LSU", "BRA"]:
                if instruction.type != "STPI": # not STPI because we still need to broad cast results for LDPI and STPI effec addr
                    cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.PRF.rob_entry(instruction.operands[0]))

                if instruction.type in {"STPI", "LDPI"}:
                    # print(f"finding corresponding rob for {instruction.operands[1]}")
                    cpu.RS[rs_type].broadcast(result=int(instruction.effective_address[-1]), rob_entry=cpu.PRF.rob_entry(instruction.base_reg))

            # broadcast result to possible awaiting stores
            if instruction.type != "STPI": cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0]) # operand zero is dst reg
        ###################

        self.instr = None
        return True
    
    def flush(self):
        self.instr = None
        self.cycle_latency = 0
        self.AVAILABLE = True
    
    def LD(self, cpu): 
        '''r1 <- MEM[regs[r2] + regs[r3]]'''

        # at this point it should have result either already filled via earlier ST in rob or not filled and just need to read
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
        if self.instr["val1"] is not None and instruction.result is None:
            instruction.result = (self.instr["val1"])

        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction
    
    def STPI(self,cpu):
        instruction = self.instr["INSTRs"]
        if self.instr["val1"] is not None and instruction.result is None:
            instruction.result = (self.instr["val1"])

        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction

    def LDPI(self,cpu):
        instruction = self.instr["INSTRs"]

        if not self.instr["INSTRs"].result:
            self.instr["INSTRs"].result = cpu.MEM.read(f"MEM{int(self.instr["val1"]) + int(self.instr["val2"])}")
        
        return instruction
