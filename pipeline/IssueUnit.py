from .Instruction import Instruction
from collections import deque

class IssueUnit:
    
    def issue(self, cpu):
        """
        issues instruction from reservation station(s) to execution units
        - happens in same cycle as execution
        """
        # stuff currently inside execution units and 
        issued_counter = 0

        for execution_unit in cpu.execute_units:
            # if there is non-busy execution unit assign an instruction if possible per super scale
            if execution_unit.AVAILABLE and issued_counter < cpu.super_scaling and execution_unit.take_instruction(cpu):
                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
            # else:
            #     print(f"   >> didn't issue to {execution_unit.RS_type}{execution_unit.ID}")



