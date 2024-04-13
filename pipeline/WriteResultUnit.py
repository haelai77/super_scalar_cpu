from .Instruction import Instruction

class WriteResultUnit:

    def writeresult(self, cpu):
        """broadcasts results to reservation stations and reorder buffer via common data bus"""

        if len(cpu.CDB):
            for _ in range(len(cpu.CDB)):
                instruction = cpu.CDB.popleft() # gets completed instuction from the CBD


                print(f"written result: {instruction}")

                ###################
                # # broadcast results to reservation stations 
                # if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                    
                #     for rs_type in ["ALU", "LSU", "BRA"]:
                #         cpu.RS[rs_type].broadcast(result=instruction.result, rob_entry=cpu.PRF.rob_entry(instruction.operands[0]))
                        
                #     # broadcast result to possible awaiting stores
                #     cpu.rob.broadcast(result=instruction.result, reg=instruction.operands[0]) # operand zero is dst reg
                ###################

                cpu.rob.writeresult(instruction, cpu)
        else:
            print("written result: nothing")

        return True
            
