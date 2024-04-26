from .ReservationStation import ReservationStation
import pandas as pd
import numpy as np

class LoadStoreBuffer(ReservationStation):
    def __init__(self, maxlen=6) -> None:
        super().__init__(maxlen)
        
        self.stations.reindex(columns =["INSTRs"    , 
                                        "tag1"      , 
                                        "tag2"      , 
                                        "tag3"      , 
                                        "val1"      ,   
                                        "val2"      ,   
                                        "val3"      ,   
                                        "immediate" ])
        self.busy = False

    #override
    def add(self, instr, cpu, bypass_on=False, eu_type=False):
        "adds entry into reservation station"

        if self.available():
            self.busy = True

            tags = [None] * 3
            vals = [None] * 3
            immediate = None
            # if LD operation we only want to read the source operands not the result operand i.e. operand 0
            operands = instr.operands[1:] if instr.type in {"LD", "LDPI"} else instr.operands 

            for i, operand in enumerate(operands):
                operand_available = cpu.PRF.get_available_operand(reg=operand, cpu=cpu) if instr.type != "LDI" else operand

                #################
                # check cdb (superscaler broadcasting fix) (if operand isn't available check cdb)
                if operand_available is False: 
                    for instruction in cpu.CDB:
                        print(instruction, instruction.operands[0], operand)
                        # skip instructions that don't write
                        if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:

                            if instruction.type not in {"STPI", "LDPI"} and instruction.operands[0] == operand:
                                operand_available = instruction.result

                            # STPI
                            elif instruction.type in {"STPI", "LDPI"}:
                                if instruction.base_reg == operand: # if base register is equal to operand reg required take effective address
                                    operand_available = instruction.effective_address

                            # #LDPI
                            # elif instruction.type in {"LDPI"}:
                            #     if instruction.base_reg == operand: # if base register is equal to operand value required take effective address
                            #         operand_available = instruction.effective_address

                            #     elif instruction.operands[0] == operand: # if resultant register is equal to operand reg take value
                            #         operand_available = instruction.result
                #################

                # set value if available
                if operand[0] == "P" and operand_available is not False:
                    vals[i] = operand_available

                # set rob tag if value not available in register file or rob
                elif operand[0] == "P" and operand_available is False:
                    tags[i] = cpu.PRF.rob_entry(reg=operand) 

                # must be immediate for LDI
                else:
                    immediate = operand

            ####################################### bypass
            bypassed = False
            if bypass_on:
                row = pd.Series({
                        "INSTRs"    : instr,
                        "tag1"      : tags[0],
                        "tag2"      : tags[1],
                        "tag3"      : tags[2],
                        "val1"      : vals[0],
                        "val2"      : vals[1],
                        "val3"      : vals[2],
                        "immediate" : immediate})
            
                # if memory is ready to have effective address calculated
                if (row["INSTRs"].type == "ST" and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu) or
                    row["INSTRs"].type == "LDI" and row["immediate"] is not None and self.non_ooo_check(row, cpu)):
                    for execution_unit in cpu.execute_units:
                        if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                            execution_unit.instr = row
                            execution_unit.AVAILABLE = False
                            execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                            bypassed = True
                            break
                    return bypassed
                
                # if load and not earlier stores with same effective address 
                elif row["INSTRs"].type == "LD" and row["val1"] is not None and row["val2"] is not None:
                    row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                    result = cpu.rob.mem_disambiguate(row["INSTRs"])

                    # return load with result from earlier store filled if possible
                    if type(result) is int and self.non_ooo_check(row, cpu):
                        row["INSTRs"].result = result
                        for execution_unit in cpu.execute_units:
                            if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                                # row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"

                                execution_unit.instr = row
                                execution_unit.AVAILABLE = False
                                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                                bypassed = True
                                break
                        return bypassed
                    # else return with result not filled but can read memory without >dependency<
                    elif result is True and self.non_ooo_check(row, cpu):
                        for execution_unit in cpu.execute_units:
                            if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                                # row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                                
                                execution_unit.instr = row
                                execution_unit.AVAILABLE = False
                                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                                bypassed = True
                                break
                        return bypassed
                else:
                    return False
    
            #######################################
            # print({
            #     "INSTRs"    : instr,
            #     "tag1"      : tags[0],
            #     "tag2"      : tags[1],
            #     "tag3"      : tags[2],
            #     "val1"      : vals[0],
            #     "val2"      : vals[1],
            #     "val3"      : vals[2],
            #     "immediate" : immediate})
            # add entry to reservation station
            self.stations = pd.concat([self.stations, pd.DataFrame([{
                                                                    "INSTRs"    : instr,
                                                                    "tag1"      : tags[0],
                                                                    "tag2"      : tags[1],
                                                                    "tag3"      : tags[2],
                                                                    "val1"      : vals[0],
                                                                    "val2"      : vals[1],
                                                                    "val3"      : vals[2],
                                                                    "immediate" : immediate}])], ignore_index=True)
            self.stations = self.stations.replace({np.nan:None})
        else:
            print(" >> reservation station full <<")
            return False

    def flush(self):
        self.stations = pd.DataFrame(columns = ["INSTRs", 
                                                "tag1"      , 
                                                "tag2"      , 
                                                "tag3"      , 
                                                "val1"      ,   
                                                "val2"      ,   
                                                "val3"      ,   
                                                "immediate" ])

    #override
    def broadcast(self, rob_entry, result):
        # # updates value entries and tag entries so that results from execution now fill the value entries of awaiting instructions
        return super().broadcast(rob_entry, result, tags=3)
        # if len(self.stations) == 0:
        #     return True
        
        # for _, row in self.stations.iterrows():
        #     start = 1
        #     if row["INSTRs"].type in {"ST", "STPI"}: # operands to be filled are in all spots
        #         end = 3 + 1
        #     elif row["INSTRs"].type in {"LD", "LDPI"}: # operands to be filled are in spots 1 and 2
        #         end = 2 + 1
        #     else: #LDI skip no broadcasting required
        #         continue
            
        #     for i in range(start, end):                     #HACK SAME ROB ENTRY BUT DIFFERENT REGISTERS, HOW CAN I CHECK?, SIMPLY ADD ANOTHER CONDITION, IF ROB ENTRY MATCHES AND REGISTER
        #         # if we are broadcasting a base_register we need to make sure that instructions waiting for corresponding rob entry are waiting for the base register and not the LDPI result
        #         if base_reg is not False:
                    
        #         #     if row[f"tag{i}"] == rob_entry and row["INSTRs"].operands[i] == base_reg:
        #         #         row[f"tag{i}"] = None
        #         #         row[f"val{i}"] = result
        #         # else:
        #         #     if row[f"tag{i}"] == rob_entry:
        #         #         row[f"tag{i}"] = None
        #         #         row[f"val{i}"] = result

        # return True
    
    def __pop_row(self, i):
        self.stations = self.stations.T
        entry = self.stations.pop(i)
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
    
    #override 
    def pop(self, cpu):
        """pops first instruction out of the reservation station if ready (can be LD, LDI or ST)"""
        # print(self.stations.to_string())
        length = len(self.stations) if cpu.ooo else 1
        if len(self.stations):
            for i in range(length):

                row = self.stations.iloc[i].copy() # todo test if this can go out of order
                # print(row)
                
                # if memory is ready to have effective address calculated
                if row["INSTRs"].type in {"ST", "STPI"} and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu):
                    return self.__pop_row(i)
                    
                # if load and not earlier stores with same effective address 
                elif row["INSTRs"].type in {"LD", "LDPI"} and row["val1"] is not None and row["val2"] is not None:
                    row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                    result = cpu.rob.mem_disambiguate(row["INSTRs"]) #NOTE loads only get popped if diambiguation is successful
                    #note: this works because it is in order
                    # # return load with result from earlier store filled if possible 
                    # if result == row["INSTRs"] and self.non_ooo_check(row, cpu):
                    #     row["INSTRs"].result = result
                    #     return self.__pop_row()
                    
                    # # else return with result not filled but can read memory without >dependency<
                    # elif result == True and self.non_ooo_check(row, cpu):
                    #     return self.__pop_row()
                    
                    # return load with result from earlier store filled if possible 
                    if type(result) is int and self.non_ooo_check(row, cpu):
                        row["INSTRs"].result = result
                        return self.__pop_row(i)
                    
                    # else return with result not filled but can read memory without >dependency<
                    elif result is True and self.non_ooo_check(row, cpu):
                        return self.__pop_row(i)
                    else: # case may activate if eariler store is still being processed
                        print(f">>>{row["INSTRs"]} not ready<<<")
                        return False
                    
                elif row["INSTRs"].type == "LDI" and row["immediate"] is not None and self.non_ooo_check(row, cpu):
                    return self.__pop_row(i)
        return False
