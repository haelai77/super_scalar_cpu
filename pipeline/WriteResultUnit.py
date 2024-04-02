from .Instruction import Instruction

class WriteResultUnit:

    def writeresult(self, cpu):
        """broadcasts results to reservation stations and reorder buffer via common data bus"""

        # TODO: load effective address calculation must occure after all earlier stores
        # TODO: if load instruction pause if there is a store instruction ahead in ROB with effective address location the same as operand address in load

        if len(cpu.CDB):
            for _ in range(cpu.super_scaling):
                instruction = cpu.CDB.popleft() # gets completed instuction from the CBD

                # write instruction result to associated rob entry
                    # in the case of stores, result = value to be stored
                    # in the case of branches there is no need to write results
                    # every other instruction requires writeresult
                print(f"written result: {instruction}")
                if instruction.type not in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                    cpu.rob.writeresult(instruction)
                

                # # set store to done if effective and res there
                # cpu.rob.writeresult(instruction)
        else:
            print("written result: nothing")
        
        return True
            
