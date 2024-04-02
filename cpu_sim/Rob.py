from collections import deque
import pandas as pd
from pandas import DataFrame

class Rob:
    def __init__(self, size=128) -> None:
        self.size = size
        self.commit_pointer = 0
        self.dispatch_pointer = 0
        self.ROB = DataFrame({
            "instr"  : [None] * size, # type of operation
            "dst"    : [None] * size, # where result goes, can be physical register e.g. P1 or MEM location e.g. MEM1
            "result" : [None] * size, # value to write back
            "done"   : [None] * size, # indicates whether instruction is finished and results can be written to dst
        })
        self.ROB.index = [f"rob{n}" for n in range(size)]

    def __len__(self):
        return abs(self.commit_pointer - self.dispatch_pointer)
    
    def check_done(self, rob_entry):
        return self.ROB.loc[rob_entry]["done"]
    
    def mem_disambiguate(self, load):
        """checks if loads have any dependencies on earlier stores as rob is acting as store buffer, returns earlier store result for LD to load"""
        count_fwds = self.ROB.index.get_loc(self.ROB.index[ self.ROB["instr"] == load][0])
        print(f"count_fwds: {count_fwds}, commit pointer: {self.commit_pointer}, dispatch pointer: {self.dispatch_pointer}")

        while count_fwds != self.commit_pointer:
            entry = self.ROB.iloc[count_fwds]
            if entry["instr"].type == "ST":
                # if effective addresses match and result is present
                if entry.dst["dst"] == load.effective_address and type(entry["result"]) == int:
                    print("dissambiguated, value to load: ", entry["result"])
                    return int(entry["result"])
                # must still be waiting on reg on value to write to mem
                elif entry.dst["dst"] == load.effective_address and type(entry["result"]) == str:
                    return False
            count_fwds -= 1
        return True # made it to the end with no stores matching 
            

    def writeresult(self, instr):
        """for writeresult to update result"""
        #todo may need to modify for branching
        if instr.type == "ST":
            done = 0 if not (instr.effective_address and instr.result) else 1

            # if instr.result not filled then don't attempt to overwrite as this ruins broadcasting
            if not instr.result:
                fields = ["dst"]
                vals   = [instr.effective_address]
            else:
                fields = ["dst", "result", "done"]
                vals = [instr.effective_address, instr.result, done]

            self.ROB.loc[self.ROB["instr"] == instr, fields] = vals
        else:
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

    def broadcast(self, reg, result):
        """broad casts to self"""
        # broadcasting values to be stored to mem for store instructions as store acts as store buffer
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == reg), "result"] = result
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == result) & (self.ROB["dst"].str.contains("MEM")), "done"] = 1

    def commit(self, cpu):
        """writes rob-entry instruction into registers and sets rob entry to none/empty """
        # if instr exists and is done
        if self.ROB.iloc[self.commit_pointer]["instr"] and self.ROB.iloc[self.commit_pointer]["done"]: # todo someone is done for store
            rob_entry = self.ROB.iloc[self.commit_pointer]
            
            # if store write to memory else write to register
            if rob_entry["instr"].type == "ST":
                print("storing here :",rob_entry["dst"])
                cpu.MEM.write(rob_entry["dst"], rob_entry["result"])
            else:
                cpu.PRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])

            print(f"Committed: {rob_entry["instr"]} dst:{rob_entry["dst"]} result:{rob_entry["result"]}")
            
            # clear rob entry
            self.ROB.iloc[self.commit_pointer] = {  "instr"    : None,
                                                    "dst"      : None,
                                                    "result"   : None,
                                                    "done"     : None,  }

            self.commit_pointer = (self.commit_pointer + 1) % self.size
            return rob_entry["instr"]
        print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
        return False

    def flush(self):
        """rolls back rob"""
        pass
            


            