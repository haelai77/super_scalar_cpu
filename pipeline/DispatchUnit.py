class DispatchUnit:
    
    def dispatch(self, cpu):
        """
        dispatches instruction from reservation station(s) to execution units
        - happens in same cycle as execution
        """
        # stuff currently inside execution units and 
        dispatch_counter = 0


        # if not ooo and not all available, this enforces only 1 execution unit runs at a time


        if not cpu.ooo and not (all(execution_unit.AVAILABLE for execution_unit in cpu.execute_units)):
            print(f"Dispatched: [] >> not ooo")
            return True

        for execution_unit in cpu.execute_units:

            if execution_unit.AVAILABLE and execution_unit.take_instruction(cpu):
                print(f"Dispatched: {execution_unit.instr["INSTRs"]} to {execution_unit.RS_type}")
                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                dispatch_counter += 1
                if not cpu.ooo:
                    print("here")
                    break
            else:
                print("Dispatched: []")

        return True
