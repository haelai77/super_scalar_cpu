from typing import TextIO

class Fetch_Unit:
    def __init__(self, cpu) -> None:
        self.cpu = cpu

    def jump(self):
        '''handles jump instructions'''
        return

    def fetch(self, num_to_fetch = 1):
        '''fetches instruction(s) from instruction cache and places them into the instruction buffer'''

        # take instruction from instruction cache
        curr_instrs = self.cpu.INSTR_CACHE[self.cpu.pc, self.cpu.pc: + num_to_fetch]
        
        # put instruction into the instruction buffer
        self.cpu.INSTR_BUFF.append(curr_instrs)


