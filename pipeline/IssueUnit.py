
class IssueUnit:
    def __init__(self) -> None:
        pass
    
    def issue(self, cpu):

        if len(cpu.IQ):
            for _ in range(cpu.super_scaling):
                if len(cpu.IQ) == 0:
                    break
                
                instr = cpu.IQ[0]
                RS_type = "ALU" 

                if instr.type in {"ST", "LD", "LDI"}: # Reservation station type is LSU
                    RS_type = "LSU"

                elif instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                    RS_type = "BRA"
                
                # check for structural hazards
                if cpu.rob.available() and cpu.RS[RS_type].available(): 
                    instr = cpu.IQ.popleft()
                    
                    # allocation instruction into rob
                    rob_entry = cpu.rob.add(instr)

                    # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                    if instr.type not in {"ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT"}: 
                        cpu.PRF.set_unready(reg=instr.operands[0])

                        # set corresponding rob entry that will write to physical register
                        cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                    

                    # add instruction to reservation station of correct type
                    cpu.RS[RS_type].add(instr, cpu)
            
                    
                    print(f"Issued: {instr} to RS_{RS_type}")
                else:
                    print(f"Issued: structural hazard >> rob:{cpu.rob.available()} >> RS:{RS_type}_{cpu.RS[RS_type].available()}")
                    return False
        else:
            print(f"Issued: []")
            return True
        
        return True
                

                
