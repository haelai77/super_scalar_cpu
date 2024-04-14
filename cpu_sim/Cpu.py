from collections import deque
from pipeline import *
from execution_units import *
import pandas as pd
import numpy as np

from .Register_File import Register_File
from .Memory import Memory
from .Rob import Rob
from .Rat import Rat
from .BTB import BTB
from RS.ReservationStation import ReservationStation
from RS.LoadStoreBuffer import LoadStoreBuffer
from RS.Branch_RS import Branch_RS
import copy

class Cpu:
    def __init__(self, instr_cache, fetch_unit, decode_unit, dispatch_unit, issue_unit, execute_units, writeresult_unit,
                 dynamic=False, stat_style="FIXED_always", dyna_style="DYNAMIC_1bit", super_scaling=1):
        self.pipelined = False

        self.flushed = False
        self.finished: int = 0
        self.instructions: int = 0
        self.PC: int = 0 # instruction pointer 
        self.RSB = deque([]) # return stack buffer, for when speculation fails

        self.pipe = deque([self.fetch]) # holds stages of execution 
        self.super_scaling = super_scaling

        self.exec_units = []
        self.clk_cycles = 0

        #pipeline
        self.fetch_unit = fetch_unit
        self.decode_unit = decode_unit
        self.issue_unit = issue_unit
        self.dispatch_unit = dispatch_unit
        self.execute_units = execute_units
        self.writeresult_unit = writeresult_unit
        self.CDB = deque()


        # registers and memory
        self.MEM: Memory = Memory()
        self.PRF: Register_File = Register_File(num_regs = 64) # architectural register file
        self.INSTR_CACHE = instr_cache # from assembler
        self.INSTR_BUFF = deque(maxlen = 64) # instruction queue for speculative fetch and decode
        
        #addons
        self.rob = Rob(size=64) # 128 entries
        self.rat = Rat(cpu=self) # frontend rat holds possible speculative state of the machine
        self.rrat = self.rat.RAT.copy(deep=True) # retirement rat for knowing which physical register to free
        self.r_freelist = self.rat.freelist.copy()
        self.rat_snap = deque([]) # snapshot queue for branches
        # branching
        self.static_BRA_style = stat_style
        self.dyna_BRA_style = dyna_style
        self.dynamic = dynamic
        self.BTB = BTB(self, size=256)

        self.RS = {
            "ALU" : ReservationStation(),
            "LSU" : LoadStoreBuffer(), 
            "BRA" : Branch_RS(),
        }

        self.debug = False

        self.transition = {
            self.fetch       : self.decode,
            self.decode      : self.issue,
            self.issue       : self.dispatch,
            self.dispatch    : self.execute,
            self.execute     : self.writeresult,
            self.writeresult : self.commit
        }

    ### pipeline functions ###
    def flush(self):
        self.rat.RAT = self.rrat.copy(deep=True)
        self.rat.freelist = self.r_freelist.copy()
        self.PC = self.RSB.popleft()
        self.RSB = deque()
        self.pipe = deque()
        self.fetch_unit.HALT = False
        self.INSTR_BUFF = deque(maxlen = 8)
        self.CDB = deque()

        for unit in self.execute_units:
            unit.flush()

        for RS in self.RS.values():
            RS.flush()

    def fetch(self, num_to_fetch = 1):
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        done = self.fetch_unit.fetch(cpu=self, num_to_fetch=num_to_fetch)
        return done

    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR also does renaming'''
        return self.decode_unit.decode(cpu=self)

    def issue(self):
        '''Issues instructions to available reservation stations and rob if possible'''
        return self.issue_unit.issue(cpu=self)
    
    def dispatch(self):
        '''issues an instruction from reservation station to execution unit'''
        self.dispatch_unit.dispatch(cpu=self)


    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        # run execution units
        for unit in self.execute_units:
            if not unit.AVAILABLE:
                unit.execute(cpu=self)

        for unit in self.execute_units:
            if unit.AVAILABLE:
                return True
        return True

    def writeresult(self):
        self.writeresult_unit.writeresult(cpu=self)
        return True

    def commit(self):
        if self.rob.commit(cpu=self):
            self.instructions += 1
        return True

    ##########################
    def print_circular_buffer(self):
        buffer = []
        print(f"comp:{self.rob.commit_pointer}, disp:{self.rob.dispatch_pointer}")
        
        for i in range(abs(self.rob.dispatch_pointer - self.rob.commit_pointer)):
            buffer.append(self.rob.ROB.iloc[(self.rob.commit_pointer + i) % self.rob.size])

        print(pd.DataFrame(buffer).replace({np.nan:None}))

    def run(self, debug, step_toggle = False, pipelined = False):
        '''runs the cpu simulation'''
        self.debug = debug
        self.pipelined = pipelined

        pipe_format = {
            self.fetch: "fetch",
            self.decode: "decode",
            self.issue: "Issue",
            self.dispatch: "Dispatch",
            self.execute: "execute",
            self.writeresult: "writeresult",
            self.commit: "commit"
        }

        print(f"debug : {self.debug}")

        while (not self.finished):
            print(f" >>> pipelined : {[pipe_format[stage] for stage in self.pipe][::-1]} <<< ")
            # if self.debug: print(f"Instruction_buffer: {self.INSTR_BUFF}")
            if self.pipelined:
                for _ in range(len(self.pipe)): # iterate through all stages in the pipe
                    stage = self.pipe.popleft()
                    stage()

                    if self.flushed:
                        self.flushed = False
                        break
                    
                    if stage != self.commit and not self.finished: # if the stage wasn't write back add the next corresponding step
                        self.pipe.append(self.transition[stage])

                # prep more fetches but not exceeding end of instr cache
                self.pipe.extend([self.fetch])
                self.clk_cycles += 1

                if self.debug:
                    print("## rsb")
                    print(self.RSB)
                    print("## BTB")
                    print(self.BTB.BTB)
                    print("## freelist")
                    print(self.rat.freelist)
                    print("## rrat")
                    print(self.rrat.iloc[:9])
                    print("## prf")
                    print(self.PRF.rf.loc[self.rrat.loc[self.rrat["Phys_reg"].apply(lambda reg: reg is not None), "Phys_reg"]])
                    print("## rob")
                    print(f"comp:{self.rob.commit_pointer}, disp:{self.rob.dispatch_pointer}")
                    self.print_circular_buffer()
                    print("## mem")
                    print(*self.MEM.mem, sep=" ")
                print(f"################################# clock: {self.clk_cycles}")
            
            else: # scalar 
                stage = self.pipe.popleft()

                if not stage():
                    self.pipe.append(stage)
                elif stage != self.commit:
                    self.pipe.append(self.transition[stage])
                else:
                    self.pipe.append(self.fetch)

                self.clk_cycles += 1
            
            if step_toggle == -1:
                pass
            elif self.clk_cycles >= step_toggle:
                new_step = input("take step:")
                if new_step:
                    step_toggle = int(new_step)


        print("FIN")
        print("##################### RREGS #####################")
        print(*[f"R{n}:{self.PRF.get_reg_val(self.rat.check(f"R{n}"))}" for n in range(32) if self.rat.check(f"R{n}")])
        # print("##################### PREGS #####################")
        # print(*self.PRF.rf["value"], sep=" ")
        print("##################### MEM #######################")
        print(*self.MEM.mem, sep=" ")
        print("#################################################")

        print("Cycles:", self.clk_cycles)
        print("Instrs:", self.instructions)
        print("IPC:", self.clk_cycles/self.instructions)

