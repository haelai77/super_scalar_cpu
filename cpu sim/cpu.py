from collections import deque
from typing import Deque
from Register_File import Register_File

from pipeline import *

class processor:
    def __init__(self, instructions, fetch_unit, decode_unit, execute_unit):
        self.finished: int = 0
        self.cycles: int = 0
        self.instructions: int = 0
        self.PC: int = 0 # instruction pointer

        #pipeline
        self.fetch_unit = Fetch_Unit.fetch_unit()
        self.decode_unit = Decode_Unit()
        self.execute_unit = Execute_Unit()
        self.writeback_unit = Writeback_Unit()

        # registers and memory
        self.RF: Register_File = Register_File(num_regs = 16) # register file  
        self.INSTR_CACHE: tuple[tuple, ...] = instructions
        self.INSTR_BUFF: Deque[tuple] = deque(maxlen = 8) # instruction buffer size: 8 ints


    ### pipeline functions ###

    def fetch(self, num_to_fetch = 1) -> int:
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        self.fetch_unit.fetch(self, num_to_fetch)
        self.pc += num_to_fetch # increase program counter to move to next instruction
        return


    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR'''
        return


    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        return
    

    ##########################

    def run(self):
        ''''''
        # read instructions into memory i.e. from instruction buffer into memory
        while(not self.finished):
            self.fetch() # fetches instruction from instruction cache and places it into the instruction buffer
            self.decode() # decodes what instruction is meant to be used
            self.execute() # do instruction
            self.instructions += 1

            cycles += 3 # assumes that fetch, decode and execute takes 1 cycle each
