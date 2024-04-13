class FetchUnit:
    '''Fetch unit handels instruction fetching'''
    def __init__(self, branch_label_map) -> None:
        self.HALT = False
        self.branch_label_map = branch_label_map

    def static_prediction(self, style, target, cpu):
        
        match style:
            case "FIXED_always":
                return 1
            case "FIXED_never":
                return 0
            case "STATIC":
                return target < cpu.PC
        return False

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
        if cpu.PC >= len(cpu.INSTR_CACHE):
            print("Fetching: [] >> PC beyond cache")
            return True
        elif len(cpu.INSTR_BUFF) == cpu.INSTR_BUFF.maxlen:
            print("Fetching: [] >> IQ full")
            return True
    

        # take instruction from instruction cache
        curr_instr = cpu.INSTR_CACHE[cpu.PC]

        # HALT if encoutered HALT instruction
        if self.HALT:
            print("Fetching: HALTED")
            return True
        # if HALT found set halt flag for next iteration
        if curr_instr[0] == "HALT":
            self.HALT = True


        # resolve branch labels
        curr_instr = self.predecode(curr_instr, cpu.PC)

        # if branch instruction check BTB
        if curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}:
            
            if cpu.dynamic:
                to_take = cpu.BTB.take(cpu.PC)
                
                # static prediction
                if to_take == "not_in_BTB":
                    taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
                    cpu.BTB.add(pc=cpu.PC, target= int(curr_instr[1][2]), taken_state=taken_state)

                    if taken_state:
                        cpu.RSB.append(cpu.PC + 1) # buffer rollback to not taken state
                        cpu.PC = int(curr_instr[1][2]) # 2nd operand i.e. target
                    else:
                        cpu.RSB.append(int(curr_instr[1][2]) + 1) # roll back to taken state

                # dynamic prediction
                elif to_take >= 0:
                    cpu.RSB.append(cpu.PC+1) # buffer rollback to not taken state
                    cpu.PC = int(to_take)
                else:
                    cpu.RSB.append(int(curr_instr[1][2])+1)

            # static prediction
            else:
                taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
                # if taken, buffer rollback to not taken path
                if taken_state:
                    cpu.RSB.append(cpu.PC+1)
                    cpu.PC = int(curr_instr[1][2]) # 3rd operand i.e. target
                else:
                    print("buffering not taken ",int(curr_instr[1][2]), cpu.PC+1)
                    cpu.RSB.append(int(curr_instr[1][2])+1)

        elif curr_instr[0] == "J":
            cpu.PC += int(curr_instr[1][0])
        elif curr_instr[0] == "B":
            cpu.PC = int(curr_instr[1][0])


        # put instruction into the instruction buffer
        cpu.INSTR_BUFF.append(curr_instr)

        print(f"Fetched: {curr_instr}")

        cpu.PC += 1
        return True



