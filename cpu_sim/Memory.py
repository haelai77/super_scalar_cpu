import numpy as np
import pandas as pd

class Memory:
    def __init__(self, size = 128) -> None: # arbitrary size memory
        self.size = size
        self.mem = pd.Series(data=[0]*size, index=[f"MEM{n}" for n in range(size)])

    def write(self, mem_loc, value):
        print(mem_loc, value)
        self.mem[mem_loc] = int(value)

    def read(self, mem_loc):
        return self.mem[mem_loc]