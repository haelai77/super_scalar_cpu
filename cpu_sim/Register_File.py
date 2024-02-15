import numpy as np

class Register_File:
    def __init__(self, num_regs = 19) -> None:
        # R0 = 0
        # R1 to R10 = temp registers
        # R11 to R18 = saved registers representing final computed results
        self.rf = np.empty(shape = (num_regs,), dtype=int)
        self.rf[0] = 0

    def write(self, idx, value):
        self.rf[idx] = value

    def read(self, idx):
        return self.rf[idx]