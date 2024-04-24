
class IssueUnit:
    def __init__(self) -> None:
        pass

    def attempt_bypass(self, cpu, instr, rs_type): # note no bypass for lsu yet
        # if rob available and execution unit of correct type is available
        if cpu.rob.available() and any(unit.AVAILABLE for unit in cpu.execute_units if unit.RS_type == rs_type) and len(cpu.RS[rs_type].stations) == 0:
            bypassed = False
            # attempt bypass
            if rs_type in {"ALU", "BRA", "LSU"}:
                bypassed = cpu.RS[rs_type].add(instr, cpu, bypass_on=cpu.rs_bypass, eu_type=rs_type)
            else:
                return False

            if bypassed:
                # input("")
                # cpu.bypass_counter += 1
                # remove instruction from instruction queue if managed to bypass successfully
                cpu.IQ.popleft()

                instr.bypassed_flag = True
                #add entry to rob
                rob_entry = cpu.rob.add(instr)

                # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                if instr.type not in {"ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT", "NOP"}: 
                    cpu.PRF.set_unready(reg=instr.operands[0])

                    # set corresponding rob entry that will write to physical register
                    cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                print("Issued (BYPASS): ", instr)
                return True
        return False

    def issue(self, cpu):
        if len(cpu.IQ):
            # for _ in range(cpu.super_scaling):
            #     if len(cpu.IQ) == 0:
            #         break
            
            instr = cpu.IQ[0]

            RS_type = "ALU" 

            if instr.type in {"ST", "LD", "LDI"}: # Reservation station type is LSU
                RS_type = "LSU"

            elif instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                RS_type = "BRA"

            #NOTE: if rs bypass on and eu free then dispatch straight away without putting stuff into rs
            if cpu.rs_bypass: # and instr.type:
                if self.attempt_bypass(cpu=cpu, instr=instr, rs_type=RS_type):
                    return True

            #doesn't bypass if rob and rs full but should be able to if execution unit 
            # check for structural hazards
            if cpu.rob.available() and cpu.RS[RS_type].available():
                # print(cpu.IQ)
                instr = cpu.IQ.popleft()
                
                # allocation instruction into rob
                rob_entry = cpu.rob.add(instr)

                # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                if instr.type not in {"ST", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT", "NOP"}: 
                    cpu.PRF.set_unready(reg=instr.operands[0])

                    # set corresponding rob entry that will write to physical register
                    cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                cpu.RS[RS_type].add(instr, cpu, bypass_on=False)
                
                print(f"Issued: {instr} to RS_{RS_type}")
            else:
                print(f"Issued: structural hazard >> rob:{cpu.rob.available()} >> RS:{RS_type}_{cpu.RS[RS_type].available()}")
                # print(cpu.RS[RS_type].stations.to_string())
                return False
        else:
            print(f"Issued: []")
            return True
        
        return True
                

                
