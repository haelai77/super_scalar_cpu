import pandas as pd
class BRANCH:
    def __init__(self, ID) -> None:
        self.RS_type = "BRA"
        self.AVAILABLE = True
        self.instr = None # can be pd series i.e. dataframe row or instruction object after execution 
        self.cycle_latency = 0
        self.ID = ID
        self.exe = {
            "BEQ"   : self.BEQ,
            "BNE"   : self.BNE,
            "BLT"   : self.BLT,
            "BGT"   : self.BGT,

            "J"     : self.J,
            "B"     : self.B,
            }
        
    def take_instruction(self, cpu):
        self.instr = cpu.RS[self.RS_type].pop(cpu)
        if type(self.instr) == pd.Series:
            self.AVAILABLE = False
            return True
        else:
            return False

    def execute(self, cpu):
        if self.cycle_latency > 1:
            self.cycle_latency -= 1
            print(f"Executing (BRA_{self.ID}): latency {self.cycle_latency}, {self.instr["INSTRs"]}")
            return False
    
        # execute instruction
        instr_type = self.instr["INSTRs"].type
        instruction = self.exe[instr_type](self.instr)
        print(f"Executed (BRA_{self.ID}): {self.instr["INSTRs"]}")

        state_change = 1 if instruction.branch_success else -1
        
        cpu.CDB.append(instruction)
        self.AVAILABLE = True
        self.instr = None
        return True

    def flush(self):
        self.instr = None
        self.cycle_latency = 0
        self.AVAILABLE = True
    
    def BEQ(self, instr):
        # in MIPS +4 to pc as to move to next 32bit/4byte instruction, then you add branch displacement 
        # in this simulator the program counter is incremented by branch displacement then 1 is added back in the cpu object
        '''branching if values in 2 registers are equal'''
        print(instr["val1"] == instr["val2"])
        if instr["val1"] == instr["val2"]:
            instr["INSTRs"].branch_success = True
        return instr["INSTRs"]
        
    def BNE(self, instr):
        '''branching if values in 2 registers are not equal'''
        if instr["val1"] != instr["val2"]:
            instr["INSTRs"].branch_success = True
        return instr["INSTRs"]
    
    def BLT(self, instr):
        '''branch if value in first register is less than '''
        if instr["val1"] < instr["val2"]:
            instr["INSTRs"].branch_success = True
        return instr["INSTRs"]

    def BGT(self, instr):
        '''branch if value in first register is greater than '''
        if instr["val1"] > instr["val2"]:
            instr["INSTRs"].branch_success = True
        return instr["INSTRs"]

    def J(self, instr):
        ''' branch based on immediate passed in '''
        instr["INSTRs"].branch_success = True
        return instr["INSTRs"]

    def B(self, instr):
        '''direct branch to address provided'''
        instr["INSTRs"].branch_success = True
        return instr["INSTRs"]