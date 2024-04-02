import numpy as np

class Instruction:
    def __init__(self, type, operands, cycle_latency) -> None:
        self.type: str = type
        self.operands = operands # decoded operands e.g. result register address, temp addresses etc

        ########## implementation attributes ##########
        self.cycle_latency = cycle_latency
        self.result = None # for CDB broadcast
        self.effective_address = None # only set for store operations
        ###############################################

    def __repr__(self):
        return f"{self.type}_{self.operands}"