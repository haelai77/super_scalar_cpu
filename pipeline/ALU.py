from .Instruction import Instruction
import pandas as pd

class ALU:
    """Executes arithemtic instructions inlcuding effective address calculations"""
    def __init__(self, ID) -> None:
        self.RS_type = "ALU"
        self.AVAILABLE = True
        self.instr = None # can be pd series i.e. dataframe row or instruction object after execution 
        self.cycle_latency = 0
        self.ID = ID

        self.exe = {
            "ADD"   : self.ADD,
            "ADDI"  : self.ADDI, # after decoding adding is the same as regs are replaced with values
            
            "SUB"   : self.SUB,

            "MUL"   : self.MUL,
            "DIV"   : self.DIV,

            "CMP"   : self.CMP,

            # "BEQ"   : self.BEQ,
            # "BNE"   : self.BNE,
            # "BLT"   : self.BLT,
            # "BGT"   : self.BGT,

            # "J"     : self.J,
            # "B"     : self.B,

            "HALT"  : self.HALT
        }

    def take_instruction(self, cpu):
        self.instr = cpu.RS[self.RS_type].pop(cpu)
        if type(self.instr) == pd.Series:
            self.AVAILABLE = False
            return True
        else:
            return False

    def execute(self, cpu):

        # wait for latency to be over
        if self.cycle_latency > 1:
            self.cycle_latency -= 1
            print(f"Executing (ALU_{self.ID}): latency {self.cycle_latency}, {self.instr["INSTRs"]}")
            return False
        print(f"Executed (ALU_{self.ID}): {self.instr["INSTRs"].type}")
        
        # if HALT instruction
        if self.instr["INSTRs"].type == "HALT" and not all(exec_unit.AVAILABLE for exec_unit in cpu.execute_units if exec_unit.ID != self.ID):
            return
        

        # execute instruction
        instr_type = self.instr["INSTRs"].type
        if self.instr["INSTRs"].type == "HALT":
            instruction = self.exe[instr_type](cpu)
            return True
        else:
            instruction = self.exe[instr_type]()

        # send result/instruction along the CDB
        cpu.CDB.append(instruction)
        self.AVAILABLE = True

        # broadcast results to reservation stations 
        if instruction.type not in {"ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT"}:
            for rs_type in ["ALU", "LSU"]: # todo include branch BRANCH
                cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.PRF.rob_entry(instruction.operands[0]))
        
        # broadcast result to possible awaiting stores
        cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0]) # operand zero is dst reg

        self.instr = None
        return True


    def ADD(self):
        '''r1 <- r2 + r3'''
        instruction  = self.instr["INSTRs"]
        instruction.result = int(self.instr["val1"]) + int(self.instr["val2"])
        return instruction

    def ADDI(self):
        '''r1 <- r2 + immediate'''
        "add immediate"
        instruction  = self.instr["INSTRs"]
        instruction.result = int(self.instr["val1"]) + int(self.instr["immediate"])
        return instruction
    
    def SUB(self):
        '''r1 <- r2 - r3'''
        instruction  = self.instr["INSTRs"]
        instruction.result = int(self.instr["val1"]) - int(self.instr["val2"])
        return instruction

    def MUL(self):
        '''r1 <- r2 * r3'''
        instruction  = self.instr["INSTRs"]
        instruction.result = int(self.instr["val1"]) * int(self.instr["val2"])
        return instruction

    def DIV(self):
        '''r1 <- r2 // r3'''
        instruction  = self.instr["INSTRs"]
        instruction.result = int(self.instr["val1"]) // int(self.instr["val2"])
        return instruction
    
    def CMP(self):
        '''compare the values in 2 registers and store result in third
            1. r1 < r2  = -1
            2. r1 > r2  =  1
            3. r1 == r2 =  0'''
        instruction  = self.instr["INSTRs"]

        if int(self.nstr["val1"]) < int(self.instr["val2"]):
            result = -1
        elif int(self.instr["val1"]) > int(self.instr["val2"]):
            result = 1
        else:
            result = 0
        
        instruction.result = result
        return instruction
    
    def HALT(self, cpu):
        '''stop!'''
        cpu.finished = True

#todo######### need to move branching to branch unit

    def BEQ(self, instr, cpu):
        # in MIPS +4 to pc as to move to next 32bit/4byte instruction, then you add branch displacement 
        # in this simulator the program counter is incremented by branch displacement then 1 is added back in the cpu object
        '''branching if values in 2 registers are equal'''
        if cpu.RF.read(instr.operands[0]) == cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])
        
    def BNE(self, instr, cpu):
        '''branching if values in 2 registers are not equal'''
        if cpu.RF.read(instr.operands[0]) != cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])
    
    def BLT(self, instr, cpu):
        '''branch if value in first register is less than '''
        if cpu.RF.read(instr.operands[0]) < cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])

    def BGT(self, instr, cpu):
        '''branch if value in first register is greater than '''
        if cpu.RF.read(instr.operands[0]) > cpu.RF.read(instr.operands[1]):
            cpu.PC = (instr.operands[2])

    def J(self, instr, cpu):
        ''' branch based on immediate passed in '''
        cpu.PC += (instr.operands[0])

    def B(self, instr, cpu):
        '''direct branch to address provided'''
        cpu.PC = instr.operands[0]


        
