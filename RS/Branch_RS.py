from .ReservationStation import ReservationStation
import numpy as np
from pandas import DataFrame

class Branch_RS(ReservationStation):
    def __init__(self, maxlen=6) -> None:
        super().__init__(maxlen)

    #override
    def __pop_row(self, index):
       
        self.stations = self.stations.T
        entry = self.stations.pop(index)
        self.stations = self.stations.T
        self.stations = self.stations.reset_index(drop=True)
        self.stations = self.stations.replace({np.nan:None})
   
        return entry

    def broadcast(self, rob_entry, result, v = False):
        return super().broadcast(rob_entry, result, tags=2)
    
    def flush(self):
        self.stations = DataFrame(columns=["INSTRs"    ,    # e.g. add, div etc
                                           "tag1"      ,    # input operand tag e.g. rob1
                                           "tag2"      ,    # input operand tag e.g. rob2
                                           "val1"      ,    # value from rob
                                           "val2"      ,    # value from rob
                                           "immediate" ])    # holds immediate and resolved addresses

    #override
    def pop(self, cpu):
        if len(self.stations):
            for i in range(len(self.stations)):
                row = self.stations.iloc[i]
                

                if (row["val1"] is not None) and (row["val2"] is not None and row["immediate"] is not None) and super().non_ooo_check(row, cpu): # cond branches
                    return self.__pop_row(i)
                elif (row["tag1"] is None and row["tag2"] is None and row["val1"] is None and row["val2"] is None and row["immediate"] is not None) and super().non_ooo_check(row, cpu): #uncond jump
                    return self.__pop_row(i)

                # if not cpu.ooo: # breaks on first loop if not ooo
                #     return False

        return False