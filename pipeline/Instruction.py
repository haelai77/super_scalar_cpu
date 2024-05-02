import numpy as np

class Instruction:
    def __init__(self, type, operands, cycle_latency) -> None:
        self.type: str = type
        self.operands = operands # decoded operands e.g. result register address, temp addresses etc

        ########## implementation attributes ##########
        self.logical_operands = None
        self.cycle_latency = cycle_latency
        self.result = None # for CDB broadcast
        self.effective_address = None # for rob write
        self.branch_success = False
        self.bypassed_flag = False
        self.pc = None
        ## phys reg location for STPI and LDPI after R2 gets read and also added to rat
        self.base_reg = None

        # vector stuff
        self.vstart = None
        self.vend = None
        self.bitpack_size = 16
        self.v_forwarding = None
        self.stride_size = None
        ###############################################

    def __repr__(self):
        if self.type in {"BGE","BLT", "BNE", "BEQ"}:
            return f"{self.pc}{self.type}_{self.operands}_{self.branch_success}"
        if self.type in {"STPI", "LDPI"}:
            return f"{self.pc}{self.type}_{self.operands}_{self.base_reg}"
        return f"{self.pc}{self.type}_{self.operands}_{self.result}"