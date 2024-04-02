from collections import deque
from pipeline import *

from .Register_File import Register_File
from .Memory import Memory
from .Rob import Rob
from .Rat import Rat
from .ReservationStation import ReservationStation
from .LoadStoreBuffer import LoadStoreBuffer

class Cpu:
    def __init__(self, instr_cache, fetch_unit, decode_unit, dispatch_unit, issue_unit, execute_units, writeresult_unit, num_of_RS=1):
        self.pipelined = False

        self.finished: int = 0
        self.instructions: int = 0
        self.PC: int = 0 # instruction pointer # todo put this in register?

        self.pipe = deque([self.fetch]) # holds stages of execution 
        self.super_scaling = 1

        self.exec_units = []
        self.clk_cycles = 0

        #pipeline
        self.fetch_unit = fetch_unit
        self.decode_unit = decode_unit
        self.dispatch_unit = dispatch_unit
        self.issue_unit = issue_unit
        self.execute_units = execute_units
        self.writeresult_unit = writeresult_unit
        self.CDB = deque()


        # registers and memory
        self.MEM: Memory = Memory()
        self.PRF: Register_File = Register_File(num_regs = 64) # architectural register file
        self.INSTR_CACHE = instr_cache # from assembler
        self.INSTR_BUFF = deque(maxlen = 8) # instruction queue for speculative fetch and decode
        
        #addons
        self.rob = Rob(size=128) # 128 entries
        self.rat = Rat(cpu=self) # frontend rat holds possible speculative state of the machine
        self.rrat = Rat(cpu=self) # retirement rat holds the non speculative state of cpu # note not used yet but will for speculation
        self.RS = {
            "ALU" : ReservationStation(),
            "LSU" : LoadStoreBuffer(), 
        }

        self.debug = False
        # stage transitions
        # self.transition = {
        #     self.fetch   : self.decode,
        #     self.decode  : self.issue,
        #     self.issue   : self.execute,
        #     self.execute : self.writeresult
        # }

        self.transition = {
            self.fetch     : self.decode,
            self.decode    : self.dispatch,
            self.dispatch  : self.execute,
            self.execute   : self.writeresult,
            self.writeresult : self.commit
        }

    ### pipeline functions ###
    def fetch(self, num_to_fetch = 1):
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        done = self.fetch_unit.fetch(cpu=self, num_to_fetch=num_to_fetch)
        self.PC += 1
        if self.debug:
            print(self.rat.RAT)
            print(self.PRF.rf)
            # print(self.PRF.rf.loc[self.PRF.rf["ready"] == None]["value"] )
            print(self.rob.ROB)
            pass
        return done

    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR also does renaming'''
        return self.decode_unit.decode(cpu=self)

    def dispatch(self):
        '''dispatches instructions to available reservation stations and rob if possible'''
        return self.dispatch_unit.dispatch(cpu=self)

    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        
        # issue instructions to execution units
        self.issue_unit.issue(cpu=self)

        # run execution units
        for unit in self.execute_units:
            if not unit.AVAILABLE:
                unit.execute(cpu=self)
        return True

    def writeresult(self):
        if self.writeresult_unit.writeresult(cpu=self):
            self.instructions += 1
        return True

    def commit(self):
        self.rob.commit(cpu=self)
        

    ##########################


    def run(self, debug, step_toggle = False, pipelined = False):
        '''runs the cpu simulation'''
        self.debug = debug
        self.pipelined = pipelined
        pipe_format = {
            self.fetch: "fetch",
            self.decode: "decode",
            self.dispatch: "dispatch",
            self.execute: "execute",
            self.writeresult: "writeresult",
            self.commit: "commit"
        }

        print(f"debug : {self.debug}")

        while (not self.finished):
            print("-----")
            print(f" >>> pipelined : {[pipe_format[stage] for stage in self.pipe]} <<< ")
            # if self.debug: print(f"Instruction_buffer: {self.INSTR_BUFF}")
            if self.pipelined:
                for _ in range(len(self.pipe)): # iterate through all stages in the pipe
                    stage = self.pipe.popleft()
                    stage()

                    if stage != self.commit and not self.finished: # if the stage wasn't write back add the next corresponding step
                        self.pipe.append(self.transition[stage])

                # prep more fetches but not exceeding end of instr cache
                self.pipe.extend([self.fetch])
                self.clk_cycles += 1

                if self.debug: print(f"----- clock: {self.clk_cycles}")
            else:
                stage = self.pipe.popleft()
                if not stage():
                    self.pipe.append(stage)
                elif stage != self.commit:
                    self.pipe.append(self.transition[stage])
                else:
                    self.pipe.append(self.fetch)

                self.clk_cycles += 1
                
            if step_toggle:
                input("take step")

        if debug == True:
            print("FIN")
            print("##################### RREGS #####################")
            print(*[f"R{n} : {self.PRF.get_reg_val(self.rat.check(f"R{n}"))}" for n in range(32) if self.rat.check(f"R{n}") != None], sep="\n")
            print("##################### PREGS #####################")
            print(*self.PRF.rf["value"], sep=" ")
            print("##################### MEM #######################")
            print(*self.MEM.mem, sep=" ")
            print("#################################################")
        print("Cycles:", self.clk_cycles)
        print("Instrs:", self.instructions)

