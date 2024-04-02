import pandas as pd
from pandas import DataFrame

class ReservationStation:
    def __init__(self, maxlen = 9) -> None:
        self.maxlen = maxlen

        self.stations = DataFrame(columns=["INSTRs"    ,    # e.g. add, div etc
                                           "tag1"      ,    # input operand tag e.g. rob1
                                           "tag2"      ,    # input operand tag e.g. rob2
                                           "val1"      ,    # value from rob
                                           "val2"      ,    # value from rob
                                           "immediate" ])    # holds immediate and resolved addresses
        
        self.busy      = False # Note: useful for bypass

    def available(self):
        if len(self.stations) < self.maxlen:
            return True
        else:
            return False
        
    def add(self, instr, cpu):
        "adds entry into reservation station"

        for _ in range(cpu.super_scaling):
            if self.available():
                self.busy = True

                tags = [None] * 2
                vals = [None] * 2
                immediate = None
                
                # if we're buffering an instruction that isn't writing anything we want to read all operands if they are registers
                operands = instr.operands if instr.type in {"BEQ", "BNE", "BLT", "BGT", "J"  , "B"} else instr.operands[1:]

                for i, operand in enumerate(operands):

                    operand_available = cpu.PRF.get_available_operand(reg=operand, cpu=cpu) if operand[0] == "P" else operand

                    # set value if available
                    if operand[0] == "P" and operand_available:
                        vals[i] = operand_available

                    # set rob tag if value not available in register file or rob
                    elif operand[0] == "P" and not operand_available:
                        tags[i] = cpu.PRF.rob_entry(reg=operand)

                    # must be an immediate i.e. for ADDI, B or J
                    else:
                        immediate = operand

                # add entry to reservation station
                self.stations = pd.concat([self.stations, pd.DataFrame([{
                                                                        "INSTRs"    : instr,
                                                                        "tag1"      : tags[0],
                                                                        "tag2"      : tags[1],
                                                                        "val1"      : vals[0],
                                                                        "val2"      : vals[1],
                                                                        "immediate" : immediate}])], ignore_index=True)
            else:
                print(" >> reservation station full <<")
                return False

    
    def broadcast(self, rob_entry, result, tags=2):
        """broadcasts rob result to awaiting instructions in reservation station entries"""
        # updates value entries and tag entries so that results from execution now fill the value entries of awaiting instructions
        print(f">> broadcasting rob_entry:{rob_entry}, result:{result} <<")
        for i in range(1, tags+1):
            self.stations.loc[ self.stations[f"tag{i}"].astype(str) == rob_entry,    f"val{i}"] = result
            self.stations.loc[ self.stations[f"tag{i}"].astype(str) == rob_entry,    f"tag{i}"] = None
        # print(f" >>> broadcast update <<<")
        # print(self.stations)
        # print(f" >>> broadcast update <<<")
        return True
    
    # def pop2(self, cpu):
    #     """pops a ready to run instruction out of the reservation station"""
    #     for _ in range(len(self.stations)):
    #         # get index of first occurence of available instruction
    #         print(type(self.stations["val1"]), type(self.stations["val2"]), type(self.stations["immediate"]))
    #         label_index = self.stations.index[(self.stations["val1"]!=None) & (self.stations["immediate"]!=None) & (self.stations["val2"]==None)].tolist()
            
    #         if len(label_index) > 0:
    #             index = self.stations.index.get_loc(label_index[0])
    #             if self.stations.iloc[index]["INSTRs"].type == "HALT" and cpu.rob.ROB.iloc[cpu.rob.commit_pointer]["instr"].type != "HALT":
    #                 return None
    #         else:
    #             return None

    #         # remove entry in reservation station dataframe and reset indexes
    #         self.stations = self.stations.T
    #         entry = self.stations.pop(index)
    #         self.stations = self.stations.T
    #         self.stations = self.stations.reset_index(drop=True)
    #         print("issuing:\n", entry)

    #         return entry
    #     print("Issuing: nothing")
    #     print(self.stations)
    #     return None
    
    def __pop_row(self, index):
        self.stations = self.stations.T
        entry = self.stations.pop(index)
        self.stations = self.stations.T
        self.stations = self.stations.reset_index(drop=True)
        return entry

    def pop(self, cpu):
        for i in range(len(self.stations)):
            row = self.stations.iloc[i]
            if (row["val1"]!=None) and (row["immediate"]!=None) and (row["val2"]==None): #ADDI (1 operand 1 immediate)
                return self.__pop_row(i)
            elif (row["val1"]!=None) and (row["val2"]!= None): # instructions with 2 operands
                return self.__pop_row(i)
            elif  self.stations.iloc[i]["INSTRs"].type == "HALT" and len(self.stations) == 1 and cpu.rob.ROB.iloc[cpu.rob.commit_pointer]["instr"].type == "HALT":
                return self.__pop_row(i)
        return False