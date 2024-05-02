from .ReservationStation import ReservationStation
import pandas as pd
import numpy as np
import warnings

# Ignore all future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class LoadStoreBuffer(ReservationStation):
    def __init__(self, maxlen=6) -> None:
        super().__init__(maxlen)
        
        self.stations.reindex(columns =["INSTRs"    , 
                                        "tag1"      , 
                                        "tag2"      , 
                                        "tag3"      , 
                                        "tag4"      , 
                                        "val1"      ,   
                                        "val2"      ,   
                                        "val3"      ,   
                                        "val4"      ,   
                                        "immediate" ])
        self.busy = False

    def bypass_helper(self, cpu, execution_unit, row, eu_type):
        if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type and self.non_ooo_check(row, cpu):
            execution_unit.instr = row
            execution_unit.AVAILABLE = False
            execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
            return True

    #override
    def add(self, instr, cpu, bypass_on=False, eu_type=False):
        "adds entry into reservation station"

        if self.available():
            self.busy = True

            tags = [None] * 4
            vals = [None] * 4
            immediate = None
            # if LD operation we only want to read the source operands not the result operand i.e. operand 0

            operands = instr.operands[1:] if instr.type in {"LD", "LDPI", "VLD", "VLDS"} else instr.operands 
            for i, operand in enumerate(operands):
                if (instr.type in {"VST", "VSTS"} and i == 0):
                    operand_available = cpu.VRF.get_available_operand(reg=operand, cpu=cpu)
                else:
                    operand_available = cpu.PRF.get_available_operand(reg=operand, cpu=cpu) if not ((instr.type == "LDI") or (instr.type == "STI" and i == 0)) else operand
                    print(f"lsb Here{operand_available}") 

                #################
                # check cdb (superscaler broadcasting fix) (if operand isn't available check cdb)
                if operand_available is False: 
                    for instruction in cpu.CDB:
                        # skip instructions that don't write
                        if instruction.type not in {"HALT", "ST", "STI", "BEQ", "BNE", "BLT", "BGT", "J", "B", "VST", "VSTS"}:

                            if instruction.type not in {"STPI", "LDPI"} and instruction.operands[0] == operand:
                                operand_available = instruction.result

                            # STPI
                            elif instruction.type in {"STPI", "LDPI"}:
                                if instruction.base_reg == operand: # if base register is equal to operand reg required take effective address
                                    operand_available = instruction.effective_address
                #################

                # set value if available
                if operand[0] in {"P", "V"} and operand_available is not False:
                    vals[i] = operand_available

                    offset = 0
                    # handle boundary settings on vector instructions
                    if instr.type in {"VST", "VSTS"}:
                        offset = 1
                    #note we set vstart and vend if possible
                    if instr.type in {"VST", "VLD"}:
                        if i == (0+offset):
                            instr.vstart = int(operand_available)
                        elif i == (1+offset) and instr.vstart is not None:
                            instr.vend = instr.vstart + int(operand_available) - 1

                    elif instr.type in {"VSTS", "VLDS"}:
                        if i == (0+offset):
                            instr.vstart = int(operand_available)
                        elif i == (1+offset):
                            instr.stride_size = int(operand_available) # note for checking stride store dependencies in rob
                        elif i == (2+offset) and instr.vstart is not None:
                            instr.vend = instr.vstart + int(operand_available) - 1

                # set rob tag if value not available in register file or rob
                elif operand[0] == "P" and operand_available is False:
                    tags[i] = cpu.PRF.rob_entry(reg=operand) 

                elif operand[0] == "V" and operand_available is False:
                    tags[i] = cpu.VRF.rob_entry(reg=operand) 

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
                        "tag4"      : tags[3],
                        "val1"      : vals[0],
                        "val2"      : vals[1],
                        "val3"      : vals[2],
                        "val4"      : vals[3],
                        "immediate" : immediate})
            
                # if memory is ready to have effective address calculated
                if (row["INSTRs"].type in {"ST", "STPI"} and row["val2"] is not None and row["val3"] is not None or
                    row["INSTRs"].type == "LDI" and row["immediate"] is not None or
                    row["INSTRs"].type == "STI" and row["val2"] is not None and row["val3"] is not None and row["immediate"] is not None):
                    for execution_unit in cpu.execute_units:
                        
                        if self.bypass_helper(cpu=cpu, execution_unit=execution_unit, row=row, eu_type=eu_type):
                            bypassed = True
                            break
                    return bypassed
                
                # if load and not earlier stores with same effective address 
                elif row["INSTRs"].type in {"LD", "LDPI"} and row["val1"] is not None and row["val2"] is not None:
                    row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                    result = cpu.rob.mem_disambiguate(row["INSTRs"])

                    # return load with result from earlier store filled if possible
                    if type(result) is int and self.non_ooo_check(row, cpu):
                        row["INSTRs"].result = result
                        for execution_unit in cpu.execute_units:
                            if self.bypass_helper(cpu=cpu, execution_unit=execution_unit, row=row, eu_type=eu_type):
                                bypassed = True
                                break
                        return bypassed
                    # else return with result not filled but can read memory without >dependency<
                    elif result is True and self.non_ooo_check(row, cpu):
                        for execution_unit in cpu.execute_units:
                            if self.bypass_helper(cpu=cpu, execution_unit=execution_unit, row=row, eu_type=eu_type):
                                bypassed = True
                                break
                        return bypassed
                    else:
                        return False
                
                elif row["INSTRs"].type in {"VLD"} and row["val1"] is not None and row["val2"] is not None:
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val2"])

                    # set vector boundaries
                    row["INSTRs"].vstart = int(row["val1"])
                    row["INSTRs"].vend = int(row["val1"]) + int(row["val2"]) - 1 # we minus 1 to include vstart itself
                    v_forwarding = cpu.rob.v_mem_disambiguate(row["INSTRs"], vstart=row["val1"], vend=row["INSTRs"].vend)
                    if v_forwarding:
                        for execution_unit in cpu.execute_units:
                            if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type and self.non_ooo_check(row, cpu):
                                row["INSTRs"].v_forwarding = v_forwarding # note these aren't actually the complete results, just dependecies found that contribute to the resultant binary
                                execution_unit.instr = row
                                execution_unit.AVAILABLE = False
                                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                                bypassed = True
                                break
                        return bypassed
                            
                elif row["INSTRs"].type in {"VST"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None:
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val3"])

                    row["INSTRs"].vstart = int(row["val2"])
                    row["INSTRs"].vend = int(row["val2"]) + int(row["val3"]) - 1
                    for execution_unit in cpu.execute_units:
                        if self.bypass_helper(cpu=cpu, execution_unit=execution_unit, row=row, eu_type=eu_type):
                            bypassed = True
                            break
                    return bypassed
                
                elif row["INSTRs"].type in {"VSTS"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None and row["val4"] is not None:
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val4"])
                    row["INSTRs"].vstart = int(row["val2"])
                    row["INSTRs"].vend = int(row["val2"]) + int(row["val4"]) - 1
                    for execution_unit in cpu.execute_units:
                        if self.bypass_helper(cpu=cpu, execution_unit=execution_unit, row=row, eu_type=eu_type):
                            bypassed = True
                            break
                    return bypassed
                
                elif row["INSTRs"].type in {"VLDS"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu):
                    # result, start, stride, vlr
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val3"])

                    v_forwarding = cpu.rob.vs_mem_disambiguate(row["INSTRs"], vstart=row["val1"], vend=row["INSTRs"].vend, stride_size=row["val3"])
                    row["INSTRs"].vstart = int(row["val1"])
                    row["INSTRs"].vend = int(row["val1"]) + int(row["val3"]) - 1
                    if v_forwarding:
                        for execution_unit in cpu.execute_units:
                            if execution_unit.AVAILABLE and execution_unit.RS_type == eu_type:
                                row["INSTRs"].v_forwarding = v_forwarding # note these aren't actually the complete results, just dependecies found that contribute to the resultant binary
                                execution_unit.instr = row
                                execution_unit.AVAILABLE = False
                                execution_unit.cycle_latency = execution_unit.instr["INSTRs"].cycle_latency
                                bypassed = True
                                break
                    return bypassed
                else:
                    return False
    
            #######################################

            self.stations = pd.concat([self.stations, pd.DataFrame([{
                                                                    "INSTRs"    : instr,
                                                                    "tag1"      : tags[0],
                                                                    "tag2"      : tags[1],
                                                                    "tag3"      : tags[2],
                                                                    "tag4"      : tags[3],
                                                                    "val1"      : vals[0],
                                                                    "val2"      : vals[1],
                                                                    "val3"      : vals[2],
                                                                    "val4"      : vals[3],
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
                                                "tag4"      , 
                                                "val1"      ,   
                                                "val2"      ,   
                                                "val3"      ,   
                                                "val4"      ,   
                                                "immediate" ])

    #override
    def broadcast(self, rob_entry, result, v = False):
        # # updates value entries and tag entries so that results from execution now fill the value entries of awaiting instructions
        super().broadcast(rob_entry, result, tags=4, v=v)
        #todo make sure to update any vstart and vend values onces ready
        for index, row in self.stations.iterrows():
            if row["INSTRs"].type == "VLD":
                # if mem address isn't none set it as vstart
                if row["val1"] is not None:
                    row["INSTRs"].vstart = int(row["val1"])

                    # if VLR isn't none and vstart isn't none set vend as vstart+vlr
                    if row["val2"] is not None:
                        row["INSTRs"].vend = int(row["val1"]) + int(row["val2"]) - 1

            elif row["INSTRs"].type == "VST":
                # if mem address isn't none set it as vstart
                if row["val2"] is not None:
                    row["INSTRs"].vstart = int(row["val2"])

                    # if VLR isn't none and vstart isn't none set vend as vstart+vlr
                    if row["val3"] is not None:
                        row["INSTRs"].vend = int(row["val2"]) + int(row["val3"]) - 1

            elif row["INSTRs"].type =="VSTS":
                if row["val2"] is not None:
                    row["INSTRs"].vstart = int(row["val2"])

                    # if VLR isn't none and vstart isn't none set vend as vstart+vlr
                    if row["val4"] is not None:
                        row["INSTRs"].vend = int(row["val2"]) + int(row["val4"]) - 1

            if row["INSTRs"].type == "VLDS":
                # if mem address isn't none set it as vstart
                if row["val1"] is not None:
                    row["INSTRs"].vstart = int(row["val1"])

                    # if VLR isn't none and vstart isn't none set vend as vstart+vlr
                    if row["val2"] is not None:
                        row["INSTRs"].vend = int(row["val1"]) + int(row["val3"]) - 1
                        



        self.stations = self.stations.replace({np.nan:None}) # NOTE JIC pandas decides to do some ultra annoying casting, sorry I decided to put multiple datatypes into ur pd.Series sakdjflakdsjflkasdjflkas
        return True


    def __pop_row(self, i):
        self.stations = self.stations.T
        entry = self.stations.pop(i)
        self.stations = self.stations.T
        self.stations = self.stations.reset_index(drop=True)
        return entry
    
    def non_ooo_check(self, row, cpu):
        if not cpu.ooo:
            if row["INSTRs"].pc == cpu.next[0] and (all(execution_unit.AVAILABLE for execution_unit in cpu.execute_units)):
                cpu.next.popleft()
                return True
            else:
                return False
        else:
            return True
    
    #override 
    def pop(self, cpu):
        """pops first instruction out of the reservation station if ready (can be LD, LDI or ST)"""
        length = len(self.stations)
        if len(self.stations):
            for i in range(length):
                
                row = self.stations.iloc[i].copy() # todo test if this can go out of order
                # if memory is ready to have effective address calculated
                # val1 and val2 are base and offset
                
                if row["INSTRs"].type in {"ST", "STPI"} and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu):
                    return self.__pop_row(i)
                #############
                elif row["INSTRs"].type == "STI" and row["val2"] is not None and row["val3"] is not None and int(row["immediate"]) is not None and self.non_ooo_check(row, cpu):
                    return self.__pop_row(i)
                #############
                # if load and not earlier stores with same effective address 
                elif row["INSTRs"].type in {"LD", "LDPI"} and row["val1"] is not None and row["val2"] is not None and self.non_ooo_check(row, cpu):
                    row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                    result = cpu.rob.mem_disambiguate(row["INSTRs"]) #NOTE loads only get popped if diambiguation is successful
                    
                    # return load with result from earlier store filled if possible 
                    if type(result) is int:
                        
                        row["INSTRs"].result = result
                        return self.__pop_row(i)
                    
                    # else return with result not filled but can read memory without >dependency<
                    elif result is True:
                        
                        return self.__pop_row(i)
                    else: # case may activate if eariler store is still being processed
                        
                        print(f">>>{row["INSTRs"]} not ready<<<")
                        return False
                    
                #############
                elif row["INSTRs"].type == "LDI" and int(row["immediate"]) is not None and self.non_ooo_check(row, cpu):
                    return self.__pop_row(i)
                #############
                elif row["INSTRs"].type in {"VLD"} and row["val1"] is not None and row["val2"] is not None and self.non_ooo_check(row, cpu):
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val2"])

                    # set vector boundaries
                    row["INSTRs"].vstart = int(row["val1"])
                    row["INSTRs"].vend = int(row["val1"]) + int(row["val2"]) - 1 # we minus 1 to include vstart itself

                    # check dependencies
                    v_forwarding = cpu.rob.v_mem_disambiguate(row["INSTRs"], vstart=row["val1"], vend=row["INSTRs"].vend)

                    if v_forwarding:
                        row["INSTRs"].v_forwarding = v_forwarding # note these aren't actually the complete results, just dependecies found that contribute to the resultant binary
                        return self.__pop_row(i)
                    else:
                        return False
                        
                #############
                elif row["INSTRs"].type in {"VST"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu):
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val3"])

                    row["INSTRs"].vstart = int(row["val2"])
                    row["INSTRs"].vend = int(row["val2"]) + int(row["val3"]) - 1

                    return self.__pop_row(i)
                #############
                
                elif row["INSTRs"].type in {"VSTS"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None and row["val4"] is not None and self.non_ooo_check(row, cpu):
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val4"])
                    row["INSTRs"].stride_size = row["val3"]

                    row["INSTRs"].vstart = int(row["val2"])
                    row["INSTRs"].vend = int(row["val2"]) + int(row["val4"]) - 1

                    return self.__pop_row(i)
                #############
                elif row["INSTRs"].type in {"VLDS"} and row["val1"] is not None and row["val2"] is not None and row["val3"] is not None and self.non_ooo_check(row, cpu):
                    cpu.vector_saftey_check(v_instr=row["INSTRs"], VLR=row["val3"])

                    # set vector boundaries
                    row["INSTRs"].vstart = int(row["val1"])
                    row["INSTRs"].vend = int(row["val1"]) + int(row["val3"]) - 1 # we minus 1 to include vstart itself
                    
                    vs_forwarding = cpu.rob.vs_mem_disambiguate(row["INSTRs"], vstart=row["val1"], vend=row["INSTRs"].vend, stride_size=row["val2"])
                    if vs_forwarding:
                        # input(f"zz {vs_forwarding}")
                        row["INSTRs"].stride_size = row["val2"]
                        row["INSTRs"].v_forwarding = vs_forwarding
                        return self.__pop_row(i)
                    else:
                        return False

        return False
