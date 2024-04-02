
class DispatchUnit:
    def __init__(self) -> None:
        pass

    def dispatch_depreciated(self, cpu):
        """
        dispatchs instruction to available reservation station
        - adds allocates rob entry to instruction
        - adds RAT entry for desination register
        - register operands swapped with values upon entry into reservation station
        """
        # if reservation station is available and rob entry available
        for _ in range(cpu.super_scaling):
            instr = cpu.INSTR_BUFF[0]

            # dispatch to reservation station for LSU -> if space in LSQ and RS
            if instr.type in {"ST", "LD", "LDI"} and cpu.lsq.available() and cpu.RS["LSU"].available():
                instr = cpu.INSTR_BUFF.popleft()
                instr.rob_entry = f"rob{cpu.lsq.dispatch_pointer}"
                cpu.lsq.add(instr) # adds instruction to lsq
                cpu.rat.add(instr) # adds instruction to rat

                # swap register operands for rat mappings
                for i, operand in enumerate(instr.operands):
                    if cpu.rat[operand] != operand:
                        instr.operand[i] = cpu.rat[operand]
                
                cpu.RS["LSU"].add(instr)

            # dispatch to reservation station for ALU -> if space in ROB and RS
            elif cpu.rob.available() and cpu.RS["ALU"].available():
                instr = cpu.INSTR_BUFF.popleft() 
                instr.rob_entry = f"rob{cpu.rob.dispatch_pointer}" # set rob entry
                cpu.rob.add(instr) # adds instruction to rob
                cpu.rat.add(instr) # adds instruction to rat

                # swap register operands for rat mappings
                for i, operand in enumerate(instr.operands):
                    if cpu.rat[operand] != operand:
                        instr.operand[i] = cpu.rat[operand]

                cpu.RS["ALU"].add(instr)

            else:
                return False

        return True
    
    def dispatch(self, cpu):
        if len(cpu.INSTR_BUFF):
            for _ in range(cpu.super_scaling):
                instr = cpu.INSTR_BUFF[0]
                RS_type = "ALU" # todo will need to add more type for branch

                if instr.type in {"ST", "LD", "LDI"}: # Reservation station type is LSU
                    RS_type = "LSU"
                
                # check for structural hazards
                if cpu.rob.available() and cpu.RS[RS_type].available(): 
                    instr = cpu.INSTR_BUFF.popleft()
                    
                    # allocation instruction into rob
                    rob_entry = cpu.rob.add(instr)

                    # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                    if instr.type not in {"ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT"}: 
                        cpu.PRF.set_unready(reg=instr.operands[0])

                        # set corresponding rob entry that will write to physical register
                        cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                    

                    # add instruction to reservation station of correct type
                    cpu.RS[RS_type].add(instr, cpu)
                    
                    print(f"Dispatched: {instr} to RS_{RS_type}")
                else:
                    print("Dispatch: structural hazard")
                    return False
        else:
            print(f"Dispatch: Nothing")
            return True
        
        return True
                

                
