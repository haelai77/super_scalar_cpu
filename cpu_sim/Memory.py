import numpy as np

class Memory:
    def __init__(self, size = 32) -> None: # arbitrary size memory
        self.size = size
        self.mem = np.empty(shape = (size,), dtype=int)

    def test_fill(self):
        # fills memory with dummy values from 0 to 31
        for i in range(0, self.size):
            self.mem[i] = i

    def write(self, idx, value):
        self.mem[idx] = value

    def read(self, idx):
        return self.mem[idx]