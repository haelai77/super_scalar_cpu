from collections import deque
import pandas as pd
from pandas import DataFrame
import numpy as np

class Rob:
    def __init__(self, size=64) -> None:
        self.size = size
        self.commit_pointer = 0
        self.dispatch_pointer = 0
        self.ROB = DataFrame({
            "instr"  : [None] * self.size, # type of operation
            "dst"    : [None] * self.size, # where result goes, can be physical register e.g. P1 or MEM location e.g. MEM1
            "result" : [None] * self.size, # value to write back
            "done"   : [None] * self.size, # indicates whether instruction is finished and results can be written to dst
        })
        self.ROB.index = [f"rob{n}" for n in range(size)]

    def __len__(self):
        return abs(self.commit_pointer - self.dispatch_pointer)
    
    def check_done(self, rob_entry):
        return self.ROB.loc[rob_entry]["done"]
    
    def mem_disambiguate(self, load):
        """checks if loads have any dependencies on earlier stores as rob is acting as store buffer, returns earlier store result for LD to load"""
        count_bkwds = self.ROB.index.get_loc(self.ROB.index[ self.ROB["instr"] == load][0])
        print(f"count_bkwds: {count_bkwds}, commit pointer: {self.commit_pointer}, dispatch pointer: {self.dispatch_pointer}")

        end = self.commit_pointer

        while count_bkwds != end:
            count_bkwds = (count_bkwds - 1 + self.size) % self.size
            entry = self.ROB.iloc[count_bkwds]
            if entry["instr"].type == "ST":
                # if effective addresses match and result is present
                if entry["dst"] == load.effective_address and type(entry["result"]) == int:
                    print("dissambiguated, value to load: ", entry["result"])
                    return int(entry["result"])
                # must still be waiting on reg on value to write to mem
                elif entry["dst"] == load.effective_address and type(entry["result"]) == str:
                    return False
        return True # made it to the end with no stores matching 
            
    def writeresult(self, instr, cpu):
        """for writeresult to update result"""

        if instr.type == "ST":
            done = 0 if not (instr.effective_address is not None and instr.result is not None) else 1
            # if instr.result not filled then don't attempt to overwrite as this ruins broadcasting
            if not instr.result:
                fields = ["dst"]
                vals   = [instr.effective_address]
            else:
                fields = ["dst", "result", "done"]
                vals = [instr.effective_address, instr.result, done]

            self.ROB.loc[self.ROB["instr"] == instr, fields] = vals

        elif instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}: # branches
            self.ROB.loc[self.ROB["instr"] == instr, "done"] = 1
            
        else: # other instrs
            self.ROB.loc[self.ROB["instr"] == instr, ["result", "done"]] = [instr.result, 1]

    def available(self):
        """checks if rob is available to accept entry"""
        return self.ROB.iloc[self.dispatch_pointer]["instr"] == None

    def add(self, instruction): # returns corresponding rob entry for dispatch
        """adds instructions to rob"""
        if self.available():
            
            # set up for broadcasting store value when read to rob entries
            result = None
            dst = "END"
            done = 0


            if instruction.type == "ST": # sets result to register so broad cast can find it and replace with value to write to memory
                result = instruction.operands[0] 
                dst = None
            elif instruction.type != "HALT": # avoids setting HALT result
                dst = instruction.operands[0] if instruction.type not in {"BEQ", "BNE", "BLT", "BGT", "J", "B"} else None

            # set up rob entry
            self.ROB.iloc[self.dispatch_pointer] = {"instr"  : instruction,
                                                    "dst"    : dst,
                                                    "result" : result,
                                                    "done"   : done}
            rob_entry = f"rob{self.dispatch_pointer}"
            self.dispatch_pointer = (self.dispatch_pointer + 1) % self.size
            return rob_entry
        return False
    
    def __get_type(self, instr):
        if instr is not None:
            return instr.type == "ST"
        else:
            return False
        
    def __apply_result(self, instr, result):
        if instr is not None and instr.type == "ST":
            instr.result = result
    
    def broadcast(self, reg, result):
        """broad casts to self"""
        # broadcasting values to be stored to mem for store instructions as store acts as store buffer

        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == reg), "instr"].apply(lambda instr: self.__apply_result(instr, result))
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == reg), "result"] = result
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == result) & (self.ROB["dst"].str.contains("MEM")), "done"] = 1

    def flush(self):
        self.commit_pointer = 0
        self.dispatch_pointer = 0
        self.ROB = DataFrame({
            "instr"  : [None] * self.size, # type of operation
            "dst"    : [None] * self.size, # where result goes, can be physical register e.g. P1 or MEM location e.g. MEM1
            "result" : [None] * self.size, # value to write back
            "done"   : [None] * self.size, # indicates whether instruction is finished and results can be written to dst
        })
        self.ROB.index = [f"rob{n}" for n in range(self.size)]

    def flush_check(self, rob_entry, cpu):
        flushed = False
        if cpu.dynamic:
            state_change = 1 if rob_entry["instr"].branch_success else -1
            if (((cpu.BTB.take(rob_entry["instr"].pc) >= 0) and (not rob_entry["instr"].branch_success)) or # we took but branch shouldn't have been taken
                ((cpu.BTB.take(rob_entry["instr"].pc) < 0) and (rob_entry["instr"].branch_success))): # we didn't take but branch should have been taken
                self.flush()
                cpu.flush()
                flushed = True
                print("     >>>flushed<<<")
            else:
                cpu.RSB.popleft()
            cpu.BTB.update(pc=rob_entry["instr"].pc, state_change=state_change)

        elif not cpu.dynamic:
            if (rob_entry["instr"].branch_success and cpu.static_BRA_style == "FIXED_never" or # we never take but was meant to
                not rob_entry["instr"].branch_success and cpu.static_BRA_style == "FIXED_always"):   # we always take but was meant to not take
                self.flush()
                cpu.flush()
                flushed = True
                print("     >>>flushed<<<")
            else:
                cpu.RSB.popleft()
        return flushed

    def commit(self, cpu):
        """writes rob-entry instruction into registers and sets rob entry to none/empty """
        ret = False

        for _ in range(cpu.super_scaling):
            if self.ROB.iloc[self.commit_pointer]["instr"] and self.ROB.iloc[self.commit_pointer]["done"]:
                rob_entry = self.ROB.iloc[self.commit_pointer]
                print(f"Committed: {rob_entry["instr"]} dst:{rob_entry["dst"]} result:{rob_entry["result"]}")            
                # if store write to memory else write to register
                if rob_entry["instr"].type == "ST":
                    cpu.MEM.write(rob_entry["dst"], rob_entry["result"])

                elif rob_entry["instr"].type in {"BEQ", "BNE", "BLT", "BGT"}:
                    # if speculation is correct continue else flush
                    if cpu.bra_pred and self.flush_check(rob_entry=rob_entry, cpu=cpu):
                        print("returning flushed")
                        cpu.flushed = True
                        #todo maybe boost cycles by 10 as flush punishment
                        return True

                elif rob_entry["instr"].type not in {"B", "J"}: # arithmetic,load,etc instructions
                    cpu.PRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])
                    
                    cpu.r_freelist.remove(rob_entry["dst"]) # remove incoming physical register mapping from retirement freelist

                    if cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"] is not None:
                        cpu.r_freelist.append(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # add old physical register mapping to retirement freelist

                    cpu.rat.free(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free physical register used by instruction that just committed i.e. look in rrat for logical register and free corresponding physical register
                    cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"] = rob_entry["dst"] # update rrat
        
                # clear rob entry
                self.ROB.iloc[self.commit_pointer] = {  "instr"    : None,
                                                        "dst"      : None,
                                                        "result"   : None,
                                                        "done"     : None,  }

                self.commit_pointer = (self.commit_pointer + 1) % self.size
                self.ROB = self.ROB.replace({np.nan:None})

                ret = True
        
        if ret:
            return ret

        print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
        return ret
        
            


            