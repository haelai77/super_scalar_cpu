from .Instruction import Instruction

class WriteResultUnit:

    def writeresult(self, cpu):
        """broadcasts results to reservation stations and reorder buffer via common data bus"""

        if len(cpu.CDB):
            for _ in range(len(cpu.CDB)):
                instruction = cpu.CDB.popleft() # gets completed instuction from the CBD
                if instruction.type in {"BEQ", "BNE", "BLT", "BGT"} and not cpu.bra_pred:
                    cpu.branch_wait = False
                    if instruction.branch_success:
                        cpu.PC = int(instruction.operands[2]) + 1

                print(f"written result: {instruction}")

                cpu.rob.writeresult(instruction, cpu)
        else:
            print("written result: nothing")

        return True
            
