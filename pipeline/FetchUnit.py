class FetchUnit:
    '''Fetch unit handels instruction fetching'''
    def __init__(self, branch_label_map) -> None:
        self.HALT = False
        self.branch_label_map = branch_label_map

    def predecode(self, instr, pc):
        """make operands machine readable [decode branch labels into numbers]"""
        operands = instr[1]
        resolved_operands = []
        for operand in operands:
            if operand in self.branch_label_map: 
                resolved_operands.append(str(self.branch_label_map[operand][0]))
            else: # handels immediate and register operands 
                resolved_operands.append(operand)
        return (instr[0], resolved_operands, pc)

    def fetch(self, cpu, num_to_fetch = 1):
        '''fetches instruction(s) from instruction cache and places them into the instruction buffer'''

        for _ in range(cpu.super_scaling):
            #######################
            if cpu.branch_wait:
                print("Fetching: [] >> waiting for branch")
                return False
            
            elif cpu.PC >= len(cpu.INSTR_CACHE):
                print("Fetching: [] >> No more")
                return True
            
            elif len(cpu.INSTR_BUFF) == cpu.INSTR_BUFF.maxlen:
                print("Fetching: [] >> BUFF full")
                return False
            #######################

            # take instruction from instruction cache
            curr_instr = cpu.INSTR_CACHE[cpu.PC]

            #######################
            # HALT if encoutered HALT instruction
            if self.HALT:
                print("Fetching: HALTED")
                return True
            # if HALT found set halt flag for next iteration
            if curr_instr[0] == "HALT":
                self.HALT = True
            #######################

            # if not branch prediction wait till branch is done
            if not cpu.bra_pred and curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}:
                cpu.branch_wait = True

            # resolve branch labels
            curr_instr = self.predecode(curr_instr, cpu.PC)

            # put instruction into the instruction buffer
            cpu.INSTR_BUFF.append(curr_instr)

            print(f"Fetched: {curr_instr}")

        return True



