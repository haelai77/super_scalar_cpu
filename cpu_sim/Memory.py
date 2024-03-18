import numpy as np

class Memory:
    def __init__(self, size = 128) -> None: # arbitrary size memory
        self.size = size
        # self.mem = np.empty(shape = (size,), dtype=int)
        self.mem = np.zeros(shape = (size,), dtype=int)

    def write(self, idx, value):
        self.mem[idx] = value

    def read(self, idx):
        return self.mem[idx]