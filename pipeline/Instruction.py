import numpy as np

class Instruction:
    def __init__(self, type, operands) -> None:
        self.type: str = type
        self.operands= operands # decoded operands e.g. result register address, temp addresses etc
        self.result = None

    