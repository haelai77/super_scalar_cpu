from .Instruction import Instruction
from collections import deque

class DispatchUnit:
    
    def dispatch(self, cpu):
        """
        dispatches instruction from reservation station(s) to execution units
        - happens in same cycle as execution
        """
        # stuff currently inside execution units and 
        dispatch_counter = 0


        # if not ooo and not all available, this enforces only 1 execution unit runs at a time
        if not cpu.ooo and (not all(execution_unit.AVAILABLE for execution_unit in cpu.execute_units) or len(cpu.next) == 0):
            print(f"Dispatched: [] >> not ooo", len(cpu.next) == 0)
            return False

        for execution_unit in cpu.execute_units:
            # if there is non-busy execution unit assign an instruction if possible per super scale
            # if execution_unit.AVAILABLE and dispatch_counter < cpu.super_scaling and execution_unit.take_instruction(cpu):
            if execution_unit.AVAILABLE and execution_unit.take_instruction(cpu):
                print(f"Dispatched: {execution_unit.instr["INSTRs"]} to {execution_unit.RS_type}")
                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                dispatch_counter += 1

        if dispatch_counter == 0 and len(cpu.INSTR_BUFF) != 0:
            print(f"Dispatched: []")
            return False
        return True
