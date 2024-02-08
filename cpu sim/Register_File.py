import numpy as np

class Register_File:
    def __init__(self, num_regs = 16) -> None:
        self.rf = np.empty(shape = (num_regs,))

    def write(self, idx, value):
        self.rf[idx] = value

    def read(self, idx):
        return self.rf[idx]