
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
                # remove instruction from instruction queue if managed to bypass successfully
                cpu.IQ.popleft()

                instr.bypassed_flag = True

                #add entry to rob
                rob_entry = cpu.rob.add(instr)

                # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                if instr.type not in {"ST", "STI", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT", "NOP", "STPI", "VST", "VLD", "VADD", "VSUB", "VDIV", "VMUL", "VSTS", "VLDS", "VDOT"}: 
                    cpu.PRF.set_unready(reg=instr.operands[0])

                    # set corresponding rob entry that will write to physical register
                    cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)

                elif instr.type in {"STPI", "LDPI"}: # different rob entry for base pointer
                    cpu.PRF.set_unready(reg=instr.base_reg) # set second register we're writing to as unready
                    cpu.PRF.set_rob_entry(reg=instr.base_reg, rob_entry=rob_entry+"_base") # set rob entry
                elif instr.type in {"VLD", "VADD", "VSUB", "VDIV", "VMUL", "VSTS", "VLDS", "VDOT"}:
                    cpu.VRF.set_unready(reg=instr.operands[0])
                    cpu.VRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                
                print("Issued (BYPASS): ", instr)
                return True
        return False

    def issue(self, cpu):
        if len(cpu.IQ):
            
            instr = cpu.IQ[0]

            RS_type = "ALU" 

            if instr.type in {"ST", "STI", "LD", "LDI", "STPI", "LDPI", "VST", "VLD", "VSTS", "VLDS"}: # Reservation station type is LSU
                RS_type = "LSU"

            elif instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                RS_type = "BRA"


            #NOTE: if rs bypass on and eu free then dispatch straight away without putting stuff into rs
            if cpu.ooo and cpu.rs_bypass: # and instr.type:
                if self.attempt_bypass(cpu=cpu, instr=instr, rs_type=RS_type):
                    return True
            #doesn't bypass if rob and rs full but should be able to if execution unit 
            # check for structural hazards
            if cpu.rob.available() and cpu.RS[RS_type].available():
                instr = cpu.IQ.popleft()
                
                # allocation instruction into rob
                rob_entry = cpu.rob.add(instr)

                # if you are writing to a regsiter you need to set ready bit in PRF/scordboard to false
                if instr.type not in {"ST", "STI", "BEQ", "BNE", "BLT", "BGT", "J", "B", "HALT", "NOP", "STPI", "VST", "VLD", "VADD", "VSUB", "VDIV", "VMUL", "VSTS", "VLDS", "VDOT"}: 
                    # set bit unready
                    # if instr.type == "ADDI" and instr.operands[0] == "P9":
                    cpu.PRF.set_unready(reg=instr.operands[0])

                    # set corresponding rob entry that will write to physical register
                    cpu.PRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)
                #######################
                #NOTE special case for STPI AND LDPI
                elif instr.type in {"STPI", "LDPI"}: # different rob entry for base pointer
                    cpu.PRF.set_unready(reg=instr.base_reg) # set second register we're writing to as unready
                    cpu.PRF.set_rob_entry(reg=instr.base_reg, rob_entry=rob_entry+"_base") # set rob entry
                #######################
                #NOTE special case for vector isntructions
                elif instr.type in {"VLD", "VADD", "VSUB", "VDIV", "VMUL", "VLDS", "VDOT"}:
                    cpu.VRF.set_unready(reg=instr.operands[0])
                    cpu.VRF.set_rob_entry(reg=instr.operands[0], rob_entry=rob_entry)

                cpu.RS[RS_type].add(instr, cpu, bypass_on=False)
                
                print(f"Issued: {instr} to RS_{RS_type}")
            else:
                print(f"Issued: structural hazard >> rob:{cpu.rob.available()} >> RS:{RS_type}_{cpu.RS[RS_type].available()}")
                return False
        else:
            print(f"Issued: []")
            return True
        
        return True
                

                
