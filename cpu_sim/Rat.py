from collections import deque
from pandas import DataFrame

class Rat:
    def __init__(self, cpu) -> None:
        self.cpu = cpu
        self.freelist = deque([f"P{n}" for n in range(1, len(cpu.PRF))]) # free physical registers by index ["P0", "P1", ...]
        self.RAT = DataFrame({"Phys_reg" : [None] * 32})
        self.RAT.index = [f"R{n}" for n in range(32)]

        self.RAT.iloc[0] = "P0"

    def __repr__(self) -> str:
        print(self.RAT.to_string())

    def check(self, logical_reg): # used in reservation station to swap out 
        """peeks at entry in mapping""" 
        return self.RAT.loc[logical_reg]["Phys_reg"]
    
    def free(self, physical_reg):
        if physical_reg is not None:
            self.freelist.append(physical_reg)


    def add(self, result_reg):
        """adds mapping from logical register to physical register"""
        logical_reg = result_reg
        physical_reg = self.freelist.popleft()

        rat_entry = self.RAT.loc[logical_reg]["Phys_reg"]

        # # todo fix this only free on commit
        # if rat_entry: # phys reg mapping is being overwritten so we add it back into the free list
        #     self.freelist.append(rat_entry)
        
        self.RAT.loc[logical_reg]["Phys_reg"] = physical_reg

        # print(f"        >> {logical_reg} mapped to {physical_reg} <<")
            

        return physical_reg
