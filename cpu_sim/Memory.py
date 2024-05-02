import numpy as np
import pandas as pd

class Memory:
    def __init__(self, size = 128) -> None: # arbitrary size memory
        self.size = size
        self.mem = pd.Series(data=[0]*size, index=[f"MEM{n}" for n in range(size)])

    def write(self, mem_loc, value):
        self.mem[mem_loc] = int(value)

    def read(self, mem_loc):
        return self.mem[mem_loc]
    
    def v_read(self, vstart, vend, stride=False, stride_size=None):
        if not stride:    
            return self.mem.iloc[vstart:vend+1].tolist()
        else:
            if stride_size is None:
                raise Exception("Stride size is None")
            else:
                vector_size = vend+1 - vstart
                return self.mem.iloc[int(vstart) : int(vstart+(vector_size-1)*stride_size+1) : int(stride_size)].tolist()
    
    def v_write(self, vstart, vend, int_list, stride=False, stride_size=None):
        if not stride:
            self.mem.iloc[vstart:vend+1] = int_list[-(vend+1 - vstart):]
        else:
            if stride_size is None:
                raise Exception("Stride size is None (w)")
            else:
                vector_size = vend+1 - vstart
                int_list = int_list[-(vend+1 - vstart):]
                # print(vector_size)

                # print(vstart,vstart+vector_size*stride_size,stride_size)
                # print(int_list)

                self.mem.iloc[int(vstart) : int(vstart+(vector_size-1)*stride_size+1) : int(stride_size)] = int_list