from collections import deque
import pandas as pd
import numpy as np


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
            "STI"  : self.STI,
            "STPI"  : self.STPI,
            "LDPI"  : self.LDPI,
            "VST"   : self.VST,
            "VLD"   : self.VLD,
            "VSTS"   : self.VSTS,
            "VLDS"   : self.VLDS,
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
        vec = True if instr_type[0] == "V" else False

        cpu.CDB.append(instruction)
        self.AVAILABLE = True

        ###################
        # broadcast results to reservation stations 
        if instruction.type not in {"HALT", "ST", "STI", "VST", "VSTS", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:
            
            for rs_type in ["ALU", "LSU", "BRA"]:
                if instruction.type != "STPI": # not STPI because we still need to broad cast results for LDPI and STPI effec addr
                    if instruction.type[0] == "V":
                        cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.VRF.rob_entry(instruction.operands[0]), v=True)
                    else:
                        cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.PRF.rob_entry(instruction.operands[0]))

                # must not be elif
                if instruction.type in {"STPI", "LDPI"}:
                    cpu.RS[rs_type].broadcast(result=int(instruction.effective_address[3:]), rob_entry=cpu.PRF.rob_entry(instruction.base_reg))

            # broadcast result to possible awaiting stores
            if instruction.type not in {"STPI"}:
                cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0], vec = vec) # operand zero is dst reg
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
        instruction.result = int(self.instr["immediate"])
        return instruction

    def ST(self, cpu):
        '''memory[regs[r2] + regs[r3]] <- rf[r1] # only done by rob if speculative'''
        instruction = self.instr["INSTRs"]

        # if there is a value able to be written back assign prep for CDB
        if self.instr["val1"] is not None and instruction.result is None:
            instruction.result = int(self.instr["val1"])

        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction
    
    def STI(self, cpu):
        """stores immediate into memory"""
        instruction = self.instr["INSTRs"]
        instruction.result = self.instr["immediate"]
        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction
    
    def STPI(self,cpu):
        instruction = self.instr["INSTRs"]
        if self.instr["val1"] is not None and instruction.result is None:
            instruction.result = int(self.instr["val1"])
        if type(self.instr["val2"]) in {str, np.str_}:
            self.instr["val2"] = int(self.instr["val2"][3:])
        instruction.effective_address = f"MEM{int(self.instr["val2"]) + int(self.instr["val3"])}"
        return instruction

    def LDPI(self,cpu):
        instruction = self.instr["INSTRs"]

        if not self.instr["INSTRs"].result:
            self.instr["INSTRs"].result = cpu.MEM.read(f"MEM{int(self.instr["val1"]) + int(self.instr["val2"])}")
        
        return instruction
    
    def VST(self,cpu):
        instruction = self.instr["INSTRs"]
        instruction.effective_address = f"MEM{self.instr["val1"]}"

        if instruction.result is None:
            instruction.result = (self.instr["val1"])
        # note vstart and vend are already set by this point for rob to write to
        return instruction
    
    def VLD(self, cpu):
        instruction = self.instr["INSTRs"]
        self.instr["INSTRs"].result = cpu.MEM.v_read(vstart=instruction.vstart, vend=instruction.vend)
        instruction.effective_address = f"MEM{self.instr["val1"]}"


        if self.instr["INSTRs"].v_forwarding is True:
            self.instr["INSTRs"].result = ("".join([bin(int(chunk))[2:].zfill(instruction.bitpack_size) for chunk in self.instr["INSTRs"].result])).zfill(64)
            return instruction
        else:
            for loc, partial_res in self.instr["INSTRs"].v_forwarding.items():
                self.instr["INSTRs"].result[loc] = partial_res # note we replace any dependecies found

        # convert each int in the results list to binaries and zfill to word size and concatenate then zfill to 64 bits
       
        self.instr["INSTRs"].result = ("".join([bin(int(chunk))[2:].zfill(instruction.bitpack_size) for chunk in self.instr["INSTRs"].result])).zfill(64)

        return instruction

        # result is currently a list of ints

    def VLDS(self, cpu):
        instruction = self.instr["INSTRs"]

        instruction.effective_address = f"MEM{self.instr["val1"]}"

        self.instr["INSTRs"].result = cpu.MEM.v_read(vstart=instruction.vstart, vend=instruction.vend, stride=True, stride_size=instruction.stride_size)

        if self.instr["INSTRs"].v_forwarding is True:
            self.instr["INSTRs"].result = ("".join([bin(int(chunk))[2:].zfill(instruction.bitpack_size) for chunk in self.instr["INSTRs"].result])).zfill(64)
            return instruction
        else:
            for loc, partial_res in self.instr["INSTRs"].v_forwarding.items():

                self.instr["INSTRs"].result[loc] = partial_res # note we replace any dependecies found
        
        self.instr["INSTRs"].result = ("".join([bin(int(chunk))[2:].zfill(instruction.bitpack_size) for chunk in self.instr["INSTRs"].result])).zfill(64)
        return instruction


    def VSTS(self, cpu):
        instruction = self.instr["INSTRs"]
        instruction.effective_address = f"MEM{self.instr["val1"]}"

        if instruction.result is None:
            instruction.result = (self.instr["val1"])
        # note vstart and vend are already set by this point for rob to write to
        return instruction