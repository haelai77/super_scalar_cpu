from collections import deque
from typing import Deque
from pipeline import *

from .Register_File import Register_File
from .Memory import Memory

class Cpu:
    def __init__(self, instr_cache, fetch_unit, decode_unit, execute_units, writeback_unit):
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
        self.execute_units = execute_units
        self.writeback_unit = writeback_unit

        # registers and memory
        self.MEM: Memory = Memory()
        self.RF: Register_File = Register_File(num_regs = 32) # register file  
        self.INSTR_CACHE = instr_cache
        self.INSTR_BUFF = deque(maxlen = 8) # instruction buffer size: 8 ints
        
        self.debug = False
        # stage transitions
        self.transition = {
            self.fetch   : self.decode,
            self.decode  : self.issue,
            self.issue   : self.execute,
            self.execute : self.writeback
        }

    ### pipeline functions ###
    def fetch(self, num_to_fetch = 1) -> int:
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        self.fetch_unit.fetch(cpu=self, num_to_fetch=num_to_fetch)
        self.PC += 1

    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR'''
        self.decode_unit.decode(cpu=self)

    def issue(self):
        '''Issues instructions to available execution units if possible'''
        if not self.decode_unit.issue(cpu=self):
            print(f"    stall: could not issue instruction || cycle:{self.clk_cycles}")

    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        for unit in self.execute_units:
            unit.execute(cpu=self)

    def writeback(self):
        if self.writeback_unit.writeback(cpu=self):
            self.instructions += 1

    ##########################

    def run(self, debug, step_toggle = False, pipelined = False):
        '''runs the cpu simulation'''
        self.debug = debug
        self.pipelined = pipelined
        print(f"pipelined : {self.pipelined}")
        print(f"debug : {self.debug}")

        

        # while(self.INSTR_CACHE[self.PC][0] != "HALT"):
        while (not self.finished):
            # if self.debug: print(f"Instruction_buffer: {self.INSTR_BUFF}")
            if self.pipelined:
                for _ in range(len(self.pipe)): # iterate through all stages in the pipe
                    stage = self.pipe.popleft()
                    stage()

                    if stage != self.writeback: # if the stage wasn't write back add the next corresponding step
                        self.pipe.append(self.transition[stage])

                # prep more fetches but not exceeding end of instr cache
                self.pipe.extend([self.fetch])
                self.clk_cycles += 1

                if self.debug: print(f"############# {len(self.pipe)} {self.super_scaling}")
            else:
                stage = self.pipe.popleft()
                stage()

                if stage != self.writeback:
                    self.pipe.append(self.transition[stage])
                else:
                    self.pipe.append(self.fetch)

                self.clk_cycles += 1
                
            if step_toggle:
                input("take step")

        if debug == True:
            print("FIN")
            print("##################### REGS ######################")
            print(*self.RF.rf, sep=" ")
            print("##################### MEM #######################")
            print(*self.MEM.mem, sep=" ")
            print("#################################################")
        print("Cycles:", self.clk_cycles)
        print("Instrs:", self.instructions)

