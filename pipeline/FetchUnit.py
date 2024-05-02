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
    
    def static_prediction(self, style, target, cpu):
        match style:
            case "FIXED_always":
                return 1
            case "FIXED_never":
                return 0
            case "STATIC":
                return target < cpu.PC# always take backwards jump
        return False
    
    def branch_prediction(self, cpu, curr_instr):
        # if branch instruction check BTB
        if curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}:
            instr_pc = curr_instr[2]

            if cpu.dynamic:
                to_take = cpu.BTB.take(instr_pc)
                
                # static prediction
                if to_take == "not_in_BTB":
                    taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
                    cpu.BTB.add(pc=instr_pc, target=int(curr_instr[1][2]), taken_state=taken_state)

                    if taken_state:
                        print("  >>x predict taken <<")
                        cpu.RSB.append(instr_pc + 1) # buffer rollback to not taken state
                        cpu.PC = int(curr_instr[1][2]) # 2nd operand i.e. target
                    else:
                        print("  >>x predict not taken <<")
                        cpu.RSB.append(int(curr_instr[1][2]) + 1) # roll back to taken state

                # dynamic prediction
                elif to_take >= 0:
                    print("  >> predict taken <<")
                    cpu.RSB.append(instr_pc + 1) # buffer rollback to not taken state
                    cpu.PC = int(to_take)
                else:
                    print("  >> predict not taken <<")
                    cpu.RSB.append(int(curr_instr[1][2])+1)

            # static prediction
            else:

                taken_state = self.static_prediction(style=cpu.static_BRA_style, target=int(curr_instr[1][2]), cpu=cpu)
                # if taken, buffer rollback to not taken path
                if taken_state:
                    cpu.RSB.append(instr_pc+1)
                    cpu.PC = int(curr_instr[1][2]) # 3rd operand i.e. target
                else:
                    print("buffering not taken ",int(curr_instr[1][2]), instr_pc+1)
                    cpu.RSB.append(int(curr_instr[1][2])+1)

    def fetch(self, cpu, num_to_fetch = 1):
        '''fetches instruction(s) from instruction cache and places them into the instruction buffer'''
        #######################
        # HALT if encoutered HALT instruction
        if self.HALT:
            print("Fetching: HALTED")
            return True
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

        # if HALT found set halt flag for next iteration
        if curr_instr[0] == "HALT":
            self.HALT = True

        if not cpu.ooo:
            cpu.next.append(cpu.PC)

        # resolve branch labels
        curr_instr = self.predecode(curr_instr, cpu.PC)
        instr_type, operands, pc = curr_instr

        # if not branch prediction wait till branch is done
        if not cpu.bra_pred and cpu.pipelined and curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}: # not sure we need to check if piplined for this
            cpu.branch_wait = True

        elif curr_instr[0] in {"BEQ", "BNE", "BGT", "BLT"}: # branch prediction
            cpu.branch_count += 1
            if cpu.bra_pred and instr_type in {"BEQ", "BNE", "BLT", "BGT"}:
                self.branch_prediction(cpu=cpu, curr_instr=(instr_type, operands, pc)) #NOTE: does branch prediction

        elif instr_type == "J":
            cpu.PC += int(operands[0])
        elif instr_type == "B":
            cpu.PC = int(operands[0])

        

        # put instruction into the instruction buffer
        cpu.INSTR_BUFF.append(curr_instr)

        print(f"Fetched: {curr_instr}")

     
        cpu.PC += 1
        return True



