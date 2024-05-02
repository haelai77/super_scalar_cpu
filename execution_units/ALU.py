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

            "VADD"  : self.VADD,
            "VMUL"  : self.VMUL,
            "VSUB"  : self.VSUB,
            "VDIV"  : self.VDIV,
            "VDOT"  : self.VDOT,

            "CMP"   : self.CMP,

            "HALT"  : self.HALT,
            "NOP"   : self.NOP
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
        
        print(f"Executed (ALU_{self.ID}): {self.instr["INSTRs"]}")
        
        # if HALT instruction
        if self.instr["INSTRs"].type == "HALT" and not all(exec_unit.AVAILABLE for exec_unit in cpu.execute_units if exec_unit.ID != self.ID):
            return
        

        # execute instruction
        instr_type = self.instr["INSTRs"].type
        if self.instr["INSTRs"].type == "HALT":
            instruction = self.exe[instr_type](cpu)
            return True
        elif self.instr["INSTRs"].type in {"VADD", "VSUB", "VMUL", "VDIV", "VDOT"}:
            instruction = self.exe[instr_type](cpu)
        else:
            instruction = self.exe[instr_type]()

        # send result/instruction along the CDB
        if instruction.type != "NOP": cpu.CDB.append(instruction)
        self.AVAILABLE = True
        
        ##################
        # broadcast results to reservation stations 
        vec = True if instruction.type[0] == "V" else False
        
        if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "NOP"}:
            
            for rs_type in ["ALU", "LSU", "BRA"]:
                if instruction.type[0] == "V":
                    cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.VRF.rob_entry(instruction.operands[0]), v=True)
                else:
                    cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.PRF.rob_entry(instruction.operands[0]))
                
            # broadcast result to possible awaiting stores
            cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0], vec=vec) # operand zero is dst reg
        ##################

        self.instr = None
        return True

    def flush(self):
        self.instr = None
        self.cycle_latency = 0
        self.AVAILABLE = True

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

        if int(self.instr["val1"]) < int(self.instr["val2"]):
            result = -1
        elif int(self.instr["val1"]) > int(self.instr["val2"]):
            result = 1
        else:
            result = 0
        
        instruction.result = result
        return instruction
    
    def VADD(self, cpu):
        # read in vectors and split into chuncks based on int bit word size
        instruction  = self.instr["INSTRs"]
        vector1 = cpu.rob.splitbin(binary=self.instr["val1"], instruction=instruction, conv_int=True)
        vector2 = cpu.rob.splitbin(binary=self.instr["val2"], instruction=instruction, conv_int=True)
        summed = list(map(sum, zip(vector1, vector2)))
        instruction.result = ("".join([bin(integer)[2:].zfill(instruction.bitpack_size) for integer in summed])).zfill(64)

        return instruction

    def VSUB(self, cpu):
        instruction  = self.instr["INSTRs"]
        vector1 = cpu.rob.splitbin(binary=self.instr["val1"], instruction=instruction, conv_int=True)
        vector2 = cpu.rob.splitbin(binary=self.instr["val2"], instruction=instruction, conv_int=True)
        summed = list(map(lambda tup: tup[0] - tup[1], zip(vector1, vector2)))
        instruction.result = ("".join([bin(integer)[2:].zfill(instruction.bitpack_size) for integer in summed])).zfill(64)

        return instruction

    def VMUL(self, cpu):
        instruction  = self.instr["INSTRs"]
        vector1 = cpu.rob.splitbin(binary=self.instr["val1"], instruction=instruction, conv_int=True)
        vector2 = cpu.rob.splitbin(binary=self.instr["val2"], instruction=instruction, conv_int=True)
        summed = list(map(lambda tup: tup[0] * tup[1], zip(vector1, vector2)))
        instruction.result = ("".join([bin(integer)[2:].zfill(instruction.bitpack_size) for integer in summed])).zfill(64)

        return instruction

    def VDIV(self, cpu):
        instruction  = self.instr["INSTRs"]
        vector1 = cpu.rob.splitbin(binary=self.instr["val1"], instruction=instruction, conv_int=True)
        vector2 = cpu.rob.splitbin(binary=self.instr["val2"], instruction=instruction, conv_int=True)
        zipped = zip(vector1, vector2)
        summed = []

        for a,b in zipped:
            if a == 0 or b == 0:
                summed.append(0)
            else:
                summed.append(a//b)
        # summed = list(map(lambda tup: tup[0] // tup[1], zip(vector1, vector2)))
        instruction.result = ("".join([bin(integer)[2:].zfill(instruction.bitpack_size) for integer in summed])).zfill(64)

        return instruction
    
    def VDOT(self, cpu):
        instruction  = self.instr["INSTRs"]
        instruction.vend = instruction.vstart # Because when we sum up it all turns into 1 element
        vector1 = cpu.rob.splitbin(binary=self.instr["val1"], instruction=instruction, conv_int=True)
        vector2 = cpu.rob.splitbin(binary=self.instr["val2"], instruction=instruction, conv_int=True)
        
        # input(f"{vector1}, {vector2}, {instruction.operands}")
        summed = sum(list(map(lambda tup: tup[0] * tup[1], zip(vector1, vector2))))
        instruction.result = bin(summed)[2:].zfill(64)

        return instruction
    
    def HALT(self, cpu):
        '''stop!'''
        cpu.finished = True

    def NOP(self):
        return self.instr["INSTRs"]
        
