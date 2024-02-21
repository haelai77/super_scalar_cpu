from collections import deque
from typing import Deque
from pipeline import *

from .Register_File import Register_File
from .Memory import Memory

class Cpu:
    def __init__(self, instr_cache, fetch_unit, decode_unit, execute_unit, writeback_unit):
        self.finished: int = 0
        self.cycles: int = 0
        self.instructions: int = 0
        self.PC: int = 0 # instruction pointer

        #pipeline
        self.fetch_unit: FetchUnit.FetchUnit = fetch_unit
        self.decode_unit: DecodeUnit.DecodeUnit = decode_unit
        self.execute_unit: ExecuteUnit.ExecuteUnit = execute_unit
        self.writeback_unit: WritebackUnit.WritebackUnit = writeback_unit

        # registers and memory
        self.MEM: Memory = Memory()
        self.RF: Register_File = Register_File(num_regs = 19) # register file  
        self.INSTR_CACHE: list[tuple] = instr_cache
        self.INSTR_BUFF: Deque[tuple] = deque(maxlen = 8) # instruction buffer size: 8 ints


    ### pipeline functions ###

    def fetch(self, num_to_fetch = 1) -> int:
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        self.fetch_unit.fetch(cpu=self, num_to_fetch=num_to_fetch)
        # self.pc += num_to_fetch # increase program counter to move to next instruction


    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR'''
        self.decode_unit.decode(cpu=self)


    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        self.execute_unit.execute(cpu=self)

    def writeback(self):
        self.writeback_unit.writeback(cpu=self)
    
    ##########################

    def run(self, debug = False):
        '''runs the cpu simulation'''
        # read instructions into memory i.e. from instruction buffer into memory
        while(not self.finished):
            self.fetch() # fetches instruction from instruction cache and places it into the instruction buffer
            self.decode() # decodes what instruction is meant to be used
            self.execute() # do instruction
            self.writeback()

            self.instructions += 1
            self.cycles += 4
            self.PC += 1
        
        if debug == True:
            print("FIN")
            print("##################### REGS ######################")
            print(*self.RF.rf, sep="\n")
            print("##################### MEM #######################")
            print(*self.MEM.mem, sep="\n")
            print("#################################################")
        print("Cycles:", self.cycles)
        print("Instrs:", self.instructions)

