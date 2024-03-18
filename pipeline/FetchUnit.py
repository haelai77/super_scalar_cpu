class FetchUnit:
    '''Fetch unit handels instruction fetching'''
    def __init__(self, debug_lines) -> None:
        self.debug_lines = debug_lines

    def fetch(self, cpu, num_to_fetch = 1):
        '''fetches instruction(s) from instruction cache and places them into the instruction buffer'''
        # take instruction from instruction cache
        curr_instrs = cpu.INSTR_CACHE[cpu.PC : cpu.PC + num_to_fetch]
        print(f"Fetching: {curr_instrs}")

        # put instruction into the instruction buffer
        cpu.INSTR_BUFF.extend(curr_instrs)



