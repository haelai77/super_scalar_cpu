class FetchUnit:
    '''Fetch unit handels instruction fetching'''
    def __init__(self) -> None:
        self.HALT = False

    def fetch(self, cpu, num_to_fetch = 1):
        '''fetches instruction(s) from instruction cache and places them into the instruction buffer'''

        if cpu.PC >= len(cpu.INSTR_CACHE):
            print("Fetching: []")
            return True
        # take instruction from instruction cache
        curr_instrs = cpu.INSTR_CACHE[cpu.PC : cpu.PC + num_to_fetch]

        # put instruction into the instruction buffer
        cpu.INSTR_BUFF.extend(curr_instrs)

        print(f"Fetched: {curr_instrs}")
        return True



