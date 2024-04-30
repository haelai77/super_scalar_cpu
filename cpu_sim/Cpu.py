from collections import deque
from pipeline import *
from execution_units import *
import pandas as pd
import numpy as np

from .Register_File import Register_File
from .Memory import Memory
from .Rob import Rob
from .Rat import Rat
from .BTB import BTB
from RS.ReservationStation import ReservationStation
from RS.LoadStoreBuffer import LoadStoreBuffer
from RS.Branch_RS import Branch_RS
import copy

class Cpu:
    def __init__(self, instr_cache, fetch_unit, decode_unit, dispatch_unit, issue_unit, execute_units, writeresult_unit, pipelined = False,
                 dynamic=False, stat_style="FIXED_always", dyna_style="DYNAMIC_1bit", super_scaling=1, ooo=False, bra_pred=False, rs_bypass=False, file=None):
        self.file = file

        self.pipelined = pipelined
        
        self.ooo = ooo
        self.next = deque([])

        self.rs_bypass=rs_bypass
        self.bypass_counter = 0 # for own entertainment
        self.ALU_byp_counter = 0
        self.LSU_byp_counter = 0
        self.BRA_byp_counter = 0

        self.branch_count = 0

        self.bra_pred = bra_pred
        self.branch_wait = False
        self.flush_counter = 0
        self.flushed = False
        self.finished: int = 0
        self.instructions: int = 0
        self.PC: int = 0 # instruction pointer 
        self.RSB = deque([]) # return stack buffer, for when speculation fails


        # self.exec_units = []
        self.clk_cycles = 0
        # self.pipe = deque([self.fetch]) # holds stages of execution 
        self.pipe = deque([self.fetch, self.decode, self.issue, self.dispatch, self.execute, self.writeresult, self.commit][::-1]) if pipelined else deque([self.fetch])
        # if pipelined: self.pipe.extend(([self.fetch, self.decode, self.issue]*super_scaling)[::-1]) # append fetch decode issue, super scaling number of times
        self.super_scaling = super_scaling

        #pipeline
        self.fetch_unit = fetch_unit
        self.decode_unit = decode_unit
        self.issue_unit = issue_unit
        self.dispatch_unit = dispatch_unit
        self.execute_units = execute_units
        self.writeresult_unit = writeresult_unit
        self.CDB = deque()


        # registers and memory
        self.MEM: Memory = Memory()
        self.PRF: Register_File = Register_File(num_regs = 64) # physical register file
        self.INSTR_CACHE = instr_cache # from assembler
        self.INSTR_BUFF = deque(maxlen = super_scaling) # instruction queue for speculative fetch and decode / stage between fetch and decode
        self.IQ         = deque(maxlen = 128) # instruction queue / stage between decode and issue

        ########## vector stuff
        #NOTE we will just have 16 bit integer elements
        self.VRF:Register_File = Register_File(num_regs=32, reg_type="V")
        #################
        
        #addons
        self.rob = Rob(size=64) # 128 entries
        self.rat = Rat(cpu=self) # frontend rat holds possible speculative state of the machine
        self.rrat = self.rat.RAT.copy(deep=True) # retirement rat for knowing which physical register to free
        self.r_freelist = self.rat.freelist.copy()
        self.vr_freelist = self.rat.v_freelist.copy()

        # branching
        self.static_BRA_style = stat_style
        self.dyna_BRA_style = dyna_style
        self.dynamic = dynamic
        self.BTB = BTB(self, size=64)

        self.RS = {
            "ALU" : ReservationStation(),
            "LSU" : LoadStoreBuffer(), 
            "BRA" : Branch_RS(),
        }

        self.debug = False

        self.transition = {
            self.fetch       : self.decode,
            self.decode      : self.issue,
            self.issue       : self.dispatch,
            self.dispatch    : self.execute,
            self.execute     : self.writeresult,
            self.writeresult : self.commit
        }

    def vector_saftey_check(self, v_instr, VLR):
        MVL = 64/v_instr.bitpack_size
        print(VLR)
        if MVL < int(VLR):
            raise Exception("Vector Length exceeds maximum vector size i.e. bits per element * vector length > register size")

    ### pipeline functions ###
    def flush(self):
        self.flush_counter += 1
        self.rat.RAT = self.rrat.copy(deep=True)
        self.rat.freelist = self.r_freelist.copy()
        self.rat.v_freelist = self.vr_freelist.copy()
        self.PC = self.RSB.popleft()
        self.next = deque([])
        self.RSB = deque()
        # self.pipe = deque()#NOTE temp 
        self.fetch_unit.HALT = False
        self.INSTR_BUFF = deque(maxlen = self.super_scaling)
        self.IQ         = deque(maxlen = 64) # instruction queue / stage between decode and issue

        self.CDB = deque()

        for unit in self.execute_units:
            unit.flush()

        for RS in self.RS.values():
            RS.flush()

    def fetch(self, num_to_fetch = 1):
        '''Gets 1 instruction from memory and places it in the instruction buffer INSTR'''
        done = self.fetch_unit.fetch(cpu=self, num_to_fetch=num_to_fetch)
        return done

    def decode(self): # decodes what the instruction is
        '''Determines what the first instruction is in the isntruction buffer INSTR also does renaming'''
        return self.decode_unit.decode(cpu=self)

    def issue(self):
        '''Issues instructions to available reservation stations and rob if possible'''
        return self.issue_unit.issue(cpu=self)
    
    def dispatch(self):
        '''issues an instruction from reservation station to execution unit'''
        ret = self.dispatch_unit.dispatch(cpu=self)
        return ret

    def execute(self):
        '''Executes the first instruction in the instruction buffer and removes it from the instruction buffer'''
        # run execution units
        for unit in self.execute_units:
            if not unit.AVAILABLE:
                unit.execute(cpu=self)
    
        if not self.pipelined:
            return all(unit.AVAILABLE for unit in self.execute_units)

        return True

    def writeresult(self):
        self.writeresult_unit.writeresult(cpu=self)
        return True

    def commit(self):
        if self.rob.commit(cpu=self):
            # self.instructions += 1
            return True
        return False

    ##########################
    def print_circular_buffer(self):
        buffer = []
        print(f"comp:{self.rob.commit_pointer}, disp:{self.rob.dispatch_pointer}")
        
        for i in range(abs(self.rob.dispatch_pointer - self.rob.commit_pointer)):
            buffer.append(self.rob.ROB.iloc[(self.rob.commit_pointer + i) % self.rob.size])

        print(pd.DataFrame(buffer).replace({np.nan:None}))

    def splitbin_wrapper(self, bin):
        return self.rob.splitbin(binary=bin, instruction=16, conv_int=True, t=True)

    def print_vector_regs(self):
        # vrf_copy = self.VRF.rf.copy().dropna(subset=["value"])
        # vrf_copy["value"] = vrf_copy["value"].apply(self.splitbin_wrapper)
        print(*[f"V{n} : {self.splitbin_wrapper(self.VRF.rf.loc[self.rrat.loc[f"V{n}"]["Phys_reg"],"value"])}" for n in range(16) if self.rrat.loc[f"V{n}"]["Phys_reg"] is not None and self.VRF.rf.loc[self.rrat.loc[f"V{n}","Phys_reg"], "ready"] ],
              sep="\n")

    def run(self, debug, step_toggle = False):
        '''runs the cpu simulation'''
        self.debug = debug
        # self.pipelined = pipelined

        pipe_format = {
            self.fetch: "fetch",
            self.decode: "decode",
            self.issue: "Issue",
            self.dispatch: "Dispatch",
            self.execute: "execute",
            self.writeresult: "writeresult",
            self.commit: "commit"
        }

        print(f"debug : {self.debug}")

        while (not self.finished):
            print(f" >>> pipelined : {[pipe_format[stage] for stage in self.pipe][::-1]} <<< ")

            if self.pipelined:
                for i in range(len(self.pipe)): # iterate through all stages in the pipe
                    # stage = self.pipe.popleft()
                    stage = self.pipe[i]
                    stage()

                    if stage in {self.fetch, self.decode, self.issue}:
                        for _ in range(self.super_scaling-1):
                            stage()

                    if self.flushed:
                        self.flushed = False
                        break
 
                # print(self.RS["BRA"].stations.to_string())
                    
                self.clk_cycles += 1

                # print(self.next)
                # print(self.rat.RAT.to_string)
                print("~~~~~~~~~~~ rob")
                self.print_circular_buffer()
                # print("~~~~~~~~~~~ regs")
                # print(*[f"R{n} : {self.rrat.loc[f"R{n}"]["Phys_reg"]} : {self.PRF.rf.loc[self.rrat.loc[f"R{n}"]["Phys_reg"],"value"]}" for n in range(32) if self.rrat.loc[f"R{n}"]["Phys_reg"] is not None and self.PRF.rf.loc[self.rrat.loc[f"R{n}","Phys_reg"], "ready"] ],
                #       sep="\n")
                print("~~~~~~~~~~~ prf")
                print(self.PRF.rf[self.PRF.rf["ready"].notnull()])
                print("~~~~~~~~~~~ VRF")
                self.print_vector_regs()
                print("~~~~~~~~~~~ mem")
                print(*self.MEM.mem, sep=" ")
                # print(self.RS["ALU"].stations.to_string())
                print(self.RS["LSU"].stations.to_string())
                # print(self.RS["BRA"].stations.to_string())

                if self.debug:
                    print("## rsb")
                    print(self.RSB)
                    print("## BTB")
                    print(self.BTB.BTB)
                    print("## freelist")
                    print(self.rat.freelist)
                    print("## rrat")
                    print(self.rrat.iloc[:9])
                    print("## prf")
                    print(self.PRF.rf.loc[self.rrat.loc[self.rrat["Phys_reg"].apply(lambda reg: reg is not None), "Phys_reg"]])
                    print("## rob")
                    self.print_circular_buffer()
                    print("## mem")
                    print(*self.MEM.mem, sep=" ")
            
            else: # scalar 
                stage = self.pipe.popleft()

                if not stage():
                    self.pipe.append(stage)
                elif stage != self.commit:
                    self.pipe.append(self.transition[stage])
                else:
                    self.pipe.append(self.fetch)

                # print("~~~~~~~~~~~ rob")
                # self.print_circular_buffer()
                # print("~~~~~~~~~~~ regs")
                # print(*[f"R{n} : {self.rrat.loc[f"R{n}"]["Phys_reg"]} : {self.PRF.rf.loc[self.rrat.loc[f"R{n}"]["Phys_reg"],"value"]}" for n in range(32) if self.rrat.loc[f"R{n}"]["Phys_reg"] is not None and self.PRF.rf.loc[self.rrat.loc[f"R{n}","Phys_reg"], "ready"] ],
                #       sep="\n")
                # print("~~~~~~~~~~~ mem")
                # print(*self.MEM.mem, sep=" ")

                self.clk_cycles += 1

            ### step mode ###
            
            if step_toggle == -1:
                pass

            elif self.clk_cycles >= step_toggle:
                new_step = input("take step:")
                if new_step:
                    step_toggle = int(new_step)

            print(f"################################# clock: {self.clk_cycles}")

        print("FIN")
        print("##################### RREGS #####################")
        print(*[f"R{n}:{self.PRF.get_reg_val(self.rat.check(f"R{n}"))}" for n in range(32) if self.rat.check(f"R{n}")])
        # print("##################### PREGS #####################")
        # print(*self.PRF.rf["value"], sep=" ")
        print("##################### VREGS #####################")
        self.print_vector_regs()
        print("##################### MEM #######################")
        print(*self.MEM.mem, sep=" ")
        print("#################################################")
        # print(self.rob.splitbin(binary=str(self.VRF.rf.loc[self.rat.check("V1"), "value"]), instruction=None, t=True, conv_int=False))
        # print(self.rob.splitbin(binary=str(self.VRF.rf.loc[self.rat.check("V1"), "value"]), instruction=None, t=True, conv_int=True))

        print("Cycles:", self.clk_cycles)
        print("Instrs:", self.instructions)
        print("IPC:", round(self.instructions/self.clk_cycles, 4))
        print("bypass_count:", self.bypass_counter)
        print("alu bypass_count:", self.ALU_byp_counter)
        print("lsu bypass_count:", self.LSU_byp_counter)
        print("bra bypass_count:", self.BRA_byp_counter)
        print("bypass_count:", self.bypass_counter)
        print(F"flush counter: {self.flush_counter}")
        print(f"acc: {(self.branch_count-self.flush_counter)/self.branch_count if self.branch_count != 0 else None}")
        print(f"super scaling: { self.super_scaling}")
        print(f"ALUs: {len([u for u in self.execute_units if u.RS_type == "ALU"])}")
        print(f"LSU: {len([u for u in self.execute_units if u.RS_type == "LSU"])}")
        print(f"BRAs: {len([u for u in self.execute_units if u.RS_type == "BRA"])}")
        print(f"stat style: {self.static_BRA_style}")
        print(f"dynamic: {self.dynamic}")
        print(f"dyna style: {self.dyna_BRA_style}")
        print(f"file: {self.file}")
        # print("## BTB")
        # print(self.BTB.BTB)


# python main.py -pipelined -ooo -rs_bypass -bra_pred -dynamic -super_scaling 4 -n_alu 4 -n_lsu 2 -n_bra 2
# python main.py 
