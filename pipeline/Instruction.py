import numpy as np

class Instruction:
    def __init__(self, type, operands, cycle_latency) -> None:
        self.type: str = type
        self.operands= operands # decoded operands e.g. result register address, temp addresses etc
        self.result = None
        self.cycle_latency = cycle_latency
        self.done = False

    def __repr__(self):
        return f"I_{self.type}_{self.operands}_{self.done}"