from .ReservationStation import ReservationStation
import pandas as pd

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
    def add(self, instr, cpu):
        "adds entry into reservation station"

        for _ in range(cpu.super_scaling):
            if self.available():
                self.busy = True

                tags = [None] * 3
                vals = [None] * 3
                immediate = None
                # if LD operation we only want to read the source operands not the result operand i.e. operand 0
                operands = instr.operands[1:] if instr.type == "LD" else instr.operands 

                for i, operand in enumerate(operands):
                    operand_available = cpu.PRF.get_available_operand(reg=operand, cpu=cpu) if instr.type != "LDI" else operand

                    #################
                    # check cdb (superscaler broadcasting fix)
                    for instruction in cpu.CDB:
                        if instruction.type not in {"HALT", "ST", "BEQ", "BNE", "BLT", "BGT", "J", "B"}:
                            if instruction.operands[0] == operand:
                                operand_available = instruction.result

                    # set value if available
                    if operand[0] == "P" and operand_available is not False:
                        vals[i] = operand_available

                    # set rob tag if value not available in register file or rob
                    elif operand[0] == "P" and operand_available is False:
                        tags[i] = cpu.PRF.rob_entry(reg=operand) 

                    # must be immediate for LDI
                    else:
                        immediate = operand

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
        return super().broadcast(rob_entry, result, tags=3)
    
    def __pop_row(self):
        self.stations = self.stations.T
        entry = self.stations.pop(0)
        self.stations = self.stations.T
        self.stations = self.stations.reset_index(drop=True)
        return entry
    
    #override 
    def pop(self, cpu):
        """pops first instruction out of the reservation station if ready (can be LD, LDI or ST)"""
        if len(self.stations):
            row = self.stations.iloc[0].copy()
            # if memory is ready to have effective address calculated
            if row["INSTRs"].type == "ST" and row["val2"] is not None and row["val3"] is not None:
                return self.__pop_row()
                
            # if load and not earlier stores with same effective address 
            elif row["INSTRs"].type == "LD" and row["val1"] is not None and row["val2"] is not None:
                row["INSTRs"].effective_address = f"MEM{int(row["val1"]) + int(row["val2"])}"
                result = cpu.rob.mem_disambiguate(row["INSTRs"])

                # return load with result from earlier store filled if possible 
                if result == row["INSTRs"]:
                    row["INSTRs"].result = result
                    return self.__pop_row()
                # else return with result not filled but can read memory without >dependency<
                elif result == True:
                    return self.__pop_row()
                else:
                    return False
                
            elif row["INSTRs"].type == "LDI" and row["immediate"] is not None:
                return self.__pop_row()
        
 
        return False