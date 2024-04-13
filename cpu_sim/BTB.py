from pandas import DataFrame
import pandas as pd

class BTB:
    def __init__(self, cpu, size=256) -> None:
        self.add_pointer = 0
        self.size = size
        self.range = (-2, 1) if cpu.dyna_BRA_style == "DYNAMIC_2bit" else (-1, 0)

        self.BTB = DataFrame({
            "PC"            : [None] * size,
            "target"  : [None] * size, # branch target # filled at decode?
            "state"         : [None] * size, # dynamic: [ -2, -1, 0, 1] or [-1, 0]
        })

    def __move_top(self, PC):
        if not any(self.BTB["PC"] == PC):
            raise ValueError("No matching PC value in the DataFrame.")

        row_index = self.BTB[self.BTB["PC"] == PC].index[0]  # Get index of first matching row
        row_to_move = self.BTB.loc[row_index]
        self.BTB = self.BTB.drop(row_index)
        self.BTB = pd.concat([pd.DataFrame(row_to_move).transpose(), self.BTB], ignore_index=True)
        self.BTB.reset_index(drop=True, inplace=True)  # Reset the indexes

    def add(self, pc, target, taken_state):
        """
        adds entry into BTB
        taken state: from static branch prediction
        """
        state = 0 if taken_state else -1

        self.BTB.iloc[self.add_pointer] = {"PC":pc, "target":target, "state":state}
        self.add_pointer = (self.add_pointer + 1) % self.size

    def take(self, pc):
        """
        checks BTB -> during fetch for speculative fetch+decode
        - checked ones are moved to top
        """
        if pc in self.BTB["PC"].unique():
            #return state if present in BTB
            row = self.BTB.loc[self.BTB["PC"] == pc].iloc[0]
            state = row["state"]
            self.__move_top(PC=pc)

            if state >= 0:
                return row["target"]
            else:
                return -3
        else:
            return "not_in_BTB"

    def update(self, pc, state_change):
        """
        update BTB once branch is resolved
        - updated ones are moved to top
        """
        #update row and move to top
        print(f"##################################state_change: {state_change}")
        self.BTB.loc[self.BTB["PC"] == pc, "state"] = max(self.range[0] , min(self.range[1], self.BTB[self.BTB["PC"] == pc].iloc[0]["state"] + state_change))
        self.__move_top(PC=pc)