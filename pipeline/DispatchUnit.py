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

        for execution_unit in cpu.execute_units:

            # if there is non-busy execution unit assign an instruction if possible per super scale
            if execution_unit.AVAILABLE and dispatch_counter < cpu.super_scaling and execution_unit.take_instruction(cpu):
                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                dispatch_counter += 1

            # if not cpu.RS[execution_unit.RS_type].stations.empty:
