import pandas as pd
from pandas import DataFrame

class ReservationStation:
    def __init__(self, maxlen = 12) -> None:
        self.maxlen = maxlen

        self.stations = DataFrame(columns=["INSTRs"    ,    # e.g. add, div etc
                                           "tag1"      ,    # input operand tag e.g. rob1
                                           "tag2"      ,    # input operand tag e.g. rob2
                                           "val1"      ,    # value from rob
                                           "val2"      ,    # value from rob
                                           "immediate" ], dtype=object)    # holds immediate and resolved addresses
        
        self.busy = False # Note: useful for bypass

    def available(self):
        if len(self.stations) < self.maxlen:
            return True
        else:
            return False
        
    def add(self, instr, cpu, bypass_on=False, eu_type=None):
        "adds entry into reservation station"

        # for _ in range(cpu.super_scaling):
        if self.available():
            self.busy = True

            tags = [None] * 2
            vals = [None] * 2
            immediate = None
            
            # if we're buffering an instruction that isn't writing anything we want to read all operands if they are registers
            operands = instr.operands if instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"} else instr.operands[1:]
            for i, operand in enumerate(operands):
                operand_available = cpu.PRF.get_available_operand(reg=operand, cpu=cpu) if operand[0] == "P" else operand
                
                #################
                # check cdb (superscaler broadcasting fix)
                for instruction in cpu.CDB:
                    if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                        if instruction.operands[0] == operand:
                            operand_available = instruction.result
                #################

                # set value if available
                if operand[0] == "P" and operand_available is not False:
                    vals[i] = int(operand_available)

                # set rob tag if value not available in register file or rob
                elif operand[0] == "P" and operand_available is False:
                    tags[i] = cpu.PRF.rob_entry(reg=operand)

                # must be an immediate i.e. for ADDI, B or J
                else:
                    immediate = operand

            ######################### BYPASS 
            bypassed = False
            if bypass_on:
                row = pd.Series({
                                "INSTRs"    : instr,
                                "tag1"      : tags[0],
                                "tag2"      : tags[1],
                                "val1"      : vals[0],
                                "val2"      : vals[1],
                                "immediate" : immediate})
                
                if row["INSTRs"].type == "NOP":
                    for execution_unit in cpu.execute_units:
                        # if execution unit is correct type and available
                        if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                            execution_unit.instr = row
                            execution_unit.AVAILABLE = False
                            execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                            bypassed = True
                            break
                    return bypassed
                
                # NOTE: bypass doesn't really work for in-order execution
                elif ((row["val1"] is not None) and (row["immediate"] is not None) and (row["val2"] is None) and self.non_ooo_check(row, cpu) or #ADDI (1 operand 1 immediate)
                    (row["val1"] is not None) and (row["val2"] is not None) and self.non_ooo_check(row, cpu) or # instructions with 2 operands
                    row["INSTRs"].type == "HALT" and len(self.stations) == 1 and cpu.rob.ROB.iloc[cpu.rob.commit_pointer]["instr"].type == "HALT" and self.non_ooo_check(row, cpu)): # HALT
                    for execution_unit in cpu.execute_units:
                        # if execution unit is correct type and available
                        if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                            execution_unit.instr = row
                            execution_unit.AVAILABLE = False
                            execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                            bypassed = True
                            break
                    return bypassed
                else:
                    return False
            #########################
            self.stations = pd.concat([self.stations, pd.DataFrame([{
                                                                    "INSTRs"    : instr,
                                                                    "tag1"      : tags[0],
                                                                    "tag2"      : tags[1],
                                                                    "val1"      : vals[0],
                                                                    "val2"      : vals[1],
                                                                    "immediate" : immediate}], dtype=object)], ignore_index=True)
            
        else:
            print(" >> reservation station full <<")
            return False

    def flush(self):
        self.stations = DataFrame(columns=["INSTRs"    ,    # e.g. add, div etc
                                           "tag1"      ,    # input operand tag e.g. rob1
                                           "tag2"      ,    # input operand tag e.g. rob2
                                           "val1"      ,    # value from rob
                                           "val2"      ,    # value from rob
                                           "immediate" ])    # holds immediate and resolved addresses
    
    def broadcast(self, rob_entry, result, tags=2):
        """broadcasts rob result to awaiting instructions in reservation station entries"""
        # updates value entries and tag entries so that results from execution now fill the value entries of awaiting instructions
        if len(self.stations) == 0:
            return True
        for i in range(1, tags+1):
            self.stations.loc[ self.stations[f"tag{i}"].astype(str) == rob_entry,    f"val{i}"] = int(result)
            self.stations.loc[ self.stations[f"tag{i}"].astype(str) == rob_entry,    f"tag{i}"] = None
        return True
    
    def __pop_row(self, index):
        self.stations = self.stations.T
        entry = self.stations.pop(index)
        self.stations = self.stations.T
        self.stations = self.stations.reset_index(drop=True)
        return entry
    
    def non_ooo_check(self, row, cpu):
        if not cpu.ooo:
            if row["INSTRs"].pc == cpu.next[0]:
                cpu.next.popleft()
                return True
            else:
                return False
        else:
            return True

    def pop(self, cpu):
        if len(self.stations):
            for i in range(len(self.stations)):
                row = self.stations.iloc[i]
                if self.stations.iloc[i]["INSTRs"].type == "NOP":
                    return self.__pop_row(i)

                if (row["val1"] is not None) and (row["immediate"] is not None) and (row["val2"] is None) and self.non_ooo_check(row, cpu): #ADDI (1 operand 1 immediate)
                    return self.__pop_row(i)
                elif (row["val1"] is not None) and (row["val2"] is not None) and self.non_ooo_check(row, cpu): # instructions with 2 operands
                    return self.__pop_row(i)
                elif  self.stations.iloc[i]["INSTRs"].type == "HALT" and len(self.stations) == 1 and cpu.rob.ROB.iloc[cpu.rob.commit_pointer]["instr"].type == "HALT" and self.non_ooo_check(row, cpu): # HALT
                    return self.__pop_row(i)
                
                if not cpu.ooo: # breaks on first loop if not ooo
                    return False

        return False