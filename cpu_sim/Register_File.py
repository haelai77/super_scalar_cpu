import numpy as np
import numpy.typing
from pandas import DataFrame


class Register_File:
    def __init__(self, num_regs = 64) -> None:
        self.num_regs = num_regs

        self.rf = DataFrame({"value"      : [None] * num_regs,
                             "ready"      : [None] * num_regs,
                             "rob_entry"  : [None] * num_regs})
        self.rf.index = [f"P{n}" for n in range(num_regs)]
        
        # keep RO and PO 
        self.rf.loc["P0"] = {"value"     : 0,
                             "ready"     : 1,
                             "rob_entry" : "zero"}
        
    def __len__(self):
        return self.num_regs
    #### ready bit setters and checkers ####
    def set_ready(self, reg):
        """sets physical register able to be read from"""
        self.rf.loc[reg]["ready"] = True
        return True
    
    def set_unready(self, reg):
        """sets physical register unable to be read from"""
        self.rf.loc[reg]["ready"] = False
        return True
    
    def check_ready(self, reg): # for checking if value in register is valid
        """checks whether physical register is ready to read from"""
        return self.rf.loc[reg]["ready"]
    ##### value getters and setters ####
    def get_reg_val(self, reg):
        """gets a value from the register"""
        return self.rf.loc[reg]["value"]
    
    def set_reg_val(self, reg, value):
        """sets a value in the register"""
        self.set_rob_entry(reg=reg, rob_entry=None)
        self.set_ready(reg=reg)
        self.rf.loc[reg]["value"] = value

        return True

    ##### rob getters and setters #####
    def set_rob_entry(self, reg, rob_entry):
        """sets corresponding rob entry"""
        self.rf.loc[reg]["rob_entry"] = rob_entry
        return True
    
    def rob_entry(self, reg):
        """finds corresponding rob entry to register file"""
        return self.rf.loc[reg]["rob_entry"]
    
    ####### deals with actual rob values #######
    def check_rob_done(self, reg, cpu):
        """checks if rob has a result in it"""
        return cpu.rob.check_done(self.rob_entry(reg=reg)) # todo fix this
    
    def get_rob_result(self, reg, cpu):
        """returns result stored in rob"""
        return cpu.rob.ROB.loc[self.rob_entry(reg)]["result"]
    
    ######## retrieve value from register or rob if available in rob
    def get_available_operand(self, reg, cpu):
        if self.check_ready(reg=reg):
            # returns register value if ready
            return self.get_reg_val(reg=reg)
        
        elif type(self.rob_entry(reg=reg)) == str and cpu.rob.check_done(self.rob_entry(reg=reg)):
            # returns rob value if ready
            return self.get_rob_result(reg=reg, cpu=cpu)
        else:
            return False


