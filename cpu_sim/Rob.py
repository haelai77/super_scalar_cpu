from collections import deque
import pandas as pd
from pandas import DataFrame
import numpy as np

class Rob:
    def __init__(self, size=64) -> None:
        self.size = size
        self.commit_pointer = 0
        self.dispatch_pointer = 0 # NOTE this should probably be called issue pointer :p
        self.ROB = DataFrame({
            "instr"  : [None] * self.size, # type of operation
            "dst"    : [None] * self.size, # where result goes, can be physical register e.g. P1 or MEM location e.g. MEM1
            "result" : [None] * self.size, # value to write back
            "done"   : [None] * self.size, # indicates whether instruction is finished and results can be written to dst
        })
        self.ROB.index = [f"rob{n}" for n in range(size)]

    def __len__(self):
        return abs(self.commit_pointer - self.dispatch_pointer)
    
    def check_done(self, rob_entry):
        rob_entry = rob_entry.split("_")[0]
        return self.ROB.loc[rob_entry]["done"]
    
    def mem_disambiguate(self, load): # 216
        """checks if loads have any dependencies on earlier stores as rob is acting as store buffer, returns earlier store result for LD to load"""
        if load not in self.ROB["instr"].unique(): # catches if flush and trying to bypass
            count_bkwds = self.dispatch_pointer
        else:
            count_bkwds = self.ROB.index.get_loc(self.ROB.index[ self.ROB["instr"] == load][0])
        # end = self.commit_pointer

        count_bkwds = (count_bkwds - 1 + self.size) % self.size
        while self.ROB.iloc[count_bkwds]["instr"] is not None:
            entry = self.ROB.iloc[count_bkwds]

            if entry["instr"].type in {"ST", "STPI"}:
                # if effective addresses match and result is present
                if entry["dst"] == load.effective_address and type(entry["result"]) == int:
                    print(">>> dissambiguated, value to load: ", entry["result"], "<<<")
                    return int(entry["result"])
                # must still be waiting on reg on value to write to mem
                elif entry["dst"] == load.effective_address and type(entry["result"]) in {str, np.str_}:
                    # print(">>> dependency found <<<")
                    return False
                
                # note if destination is None Return False
                elif entry["dst"] is None:
                    print(">>> Earlier Store hasn't completed EF calc <<<")
                    return False
            #note HANDLE LD DEPENDENCY ON VST
            if entry["instr"].type == "VST" and entry["instr"].vstart is not None and entry["instr"].vend is not None and entry["instr"].result is not None:
                if entry["instr"].vstart <= int(entry["instr"].effective_address[3:]) <= entry["instr"].vend:
                    if entry["result"][0] == "V":
                        return False
                    bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-(entry["instr"].vend+1-entry["instr"].vstart):] # note remove non necessary leasing zeros
                    return bin_words[int(entry["instr"].effective_address[3:]) - entry["instr"].vstart] # we need vstart 
                
            elif entry["instr"].type == "VST" and entry["instr"].vstart is None and entry["instr"].vend is None and entry["instr"].result is not None:
                return False
            
            #note handle VSTS
            elif entry["instr"].type == "VSTS" and entry["instr"].vstart is not None and entry["instr"].vend is not None:
                if entry["result"][0] == "V":
                    return False
                store_vector_size = entry["instr"].vend + 1 - entry["instr"].vstart
                store_points =  [i for i in range(entry["instr"].vstart, entry["instr"].vstart+(store_vector_size-1)*entry["instr"].stride_size+1, entry["instr"].stride_size)]# fixme (vectorsize-1)*stride+1 <- the minus one accounts for first item at "0"
                bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-store_vector_size:]# note we remove non necessary leading zeros for correct store_point index usage

                for point in store_points:
                    if point == int(entry["instr"].effective_address[3:]):
                        return bin_words[store_points.index(point)]

            count_bkwds = (count_bkwds - 1 + self.size) % self.size

        return True # made it to the end with no stores matching
    
    def v_mem_disambiguate(self, vload, vstart, vend):
        """for VLD"""
        if vload not in self.ROB["instr"].unique(): # catches if flush and trying to bypass
            count_bkwds = self.dispatch_pointer
        else:
            count_bkwds = self.ROB.index.get_loc(self.ROB.index[ self.ROB["instr"] == vload][0])

        count_bkwds = (count_bkwds - 1 + self.size) % self.size

        dependency_results = {}

        while self.ROB.iloc[count_bkwds]["instr"] is not None:
            entry = self.ROB.iloc[count_bkwds]
            ########################
            #note if the store is within the bounds of the vector load
            if entry["instr"].type in {"ST", "STPI"}:
                #note if the store hasn't got an effective address yet or the result isn't ready yet return false
                if entry["dst"] is None:
                    return False
                #note if the store is within loading bounds and there is a result and destination return result mapping
                elif vstart <= int(entry["dst"][3:]) <= vend and type(entry["result"]) == int:

                    if (int(entry["dst"][3:])-vstart) not in dependency_results: # only take latest dependency
                        
                        dependency_results[int(entry["dst"][3:])-vstart] = int(entry["result"])


                #note if the store is within loading bounds but there isn't a result yet return false
                elif vstart <= int(entry["dst"][3:]) <= vend and type(entry["result"]) in {str, np.str_}:
                    return False
            #######################
            #note if VST encountered and start and end is present and the result is ready i.e. not a string
            elif entry["instr"].type == "VST" and entry["instr"].vstart is not None and entry["instr"].vend is not None:
                if entry["result"][0] == "V":
                    return False
                
                # x_start <= y_end && y_start <= x_end
                if vstart <= entry["Instr"].vend and entry["Instr"].start <= vend:

                    vst_vector_size = entry["result"].vend + 1 - entry["result"].vstart
                    bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-vst_vector_size:]# note bit upacking + converting to int (we remove non necessary leading zeros)

                    # iterate through overlapping sections and add entries to dependencies
                    for i in range(max(vstart, entry["instr"].start), min(vend, entry["instr"].vend) + 1): # iterate through overlapping range
                        if (i-vstart) not in dependency_results: 
                            dependency_results[i-vstart] = bin_words[i]

            elif entry["instr"].type == "VST" and (entry["instr"].vstart is None or entry["instr"].vend is None):
                return False
            ########################
            # note watch out for VSTS
            elif entry["instr"].type == "VSTS" and entry["instr"].vstart is not None and entry["instr"].vend is not None and entry["instr"].stride_size is not None:
                if entry["result"][0] == "V":
                    return False
                
                store_vector_size = entry["instr"].vend + 1 - entry["instr"].start
                read_points =  [i for i in range(entry["instr"].vstart, entry["instr"].vstart + ((store_vector_size-1)*entry["instr"].stride_size+1), entry["instr"].stride_size)] # fixme
                bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-store_vector_size:]

                for point in read_points: # iterate through store points
                    if vstart <= point <= vend and point-vstart not in dependency_results: # if point within vector range
                        dependency_results[point-vstart] = bin_words[read_points.index(point)]
            elif entry["instr"].type == "VSTS" and (entry["instr"].vstart is None or entry["instr"].vend is None or entry["instr"].stride_size is None):
                return False
            ########################
            count_bkwds = (count_bkwds - 1 + self.size) % self.size
        return dependency_results if dependency_results else True
    
    def vs_mem_disambiguate(self, vload, vstart, vend, stride_size=None):
        """for VLDS"""
        if vload not in self.ROB["instr"].unique(): # catches if flush and trying to bypass
            count_bkwds = self.dispatch_pointer
        else:
            count_bkwds = self.ROB.index.get_loc(self.ROB.index[ self.ROB["instr"] == vload][0])

        count_bkwds = (count_bkwds - 1 + self.size) % self.size

        dependency_results = {}
        vector_size = vend+1 - vstart
        conflict_points = [i for i in range(vload.vstart, vload.vstart+(vector_size-1)*stride_size+1, stride_size)] # locations where vload will write

        while self.ROB.iloc[count_bkwds]["instr"] is not None:
            entry = self.ROB.iloc[count_bkwds]
            ######################
            if entry["instr"].type in {"ST", "STPI"}:
                if entry["dst"] is None:
                    return False
                # add to result to dependecies
                elif int(entry["dst"][3:]) in conflict_points and int(entry["dst"][3:])-vstart not in dependency_results:
                    dependency_results[int(entry["dst"][3:])-vstart] = int(entry["result"])
                # store result empty return
                elif int(entry["dst"][3:]) in conflict_points and type(entry["result"]) in {str, np.str_}:
                    return False
            ######################
            elif entry["instr"].type == "VST" and entry["instr"].vstart is not None and entry["instr"].vend is not None and entry["result"] is not None:
                if entry["result"][0] == "V":
                    return False

                vst_vector_size = entry["instr"].vend+1-entry["instr"].vstart
                bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-vst_vector_size:] # splitting the vst binary up into an int list represenataion

                for i in range(entry["instr"].vstart, entry["instr"].vend + 1): # iterate through vst range
                    if i in conflict_points and i not in dependency_results: # if point in vst matches point we will load from 
                        dependency_results[conflict_points.index(i)] = bin_words[i] 

            elif entry["instr"].type == "VST" and (entry["instr"].vstart is None or entry["instr"].vend is None or entry["result"] is None):
                return False
            ######################
            elif entry["instr"].type == "VSTS" and entry["instr"].vstart is not None and entry["instr"].vend is not None and entry["instr"].stride_size is not None and entry["result"] is not None: # todo and result is not None
                if entry["result"][0] == "V":
                    return False
                store_vector_size = entry["instr"].vend + 1 - entry["instr"].vstart
                store_points =  [i for i in range(entry["instr"].vstart, entry["instr"].vstart+(store_vector_size-1)*entry["instr"].stride_size+1, entry["instr"].stride_size)] # fixme
                bin_words = self.splitbin(entry["result"], entry["instr"], conv_int=True)[-store_vector_size:]

                # print(store_points, entry["instr"].vstart,    entry["instr"].vstart+store_vector_size*entry["instr"].stride_size,   entry["instr"].stride_size, store_vector_size)
                # print(conflict_points, vload.vstart, vload.vstart+vector_size*stride_size, stride_size, vector_size)

                # if conflict point is in store point add corresponding int at store point to dependencies 
                for point in conflict_points:
                    if point in store_points and point not in dependency_results:
                        dependency_results[conflict_points.index(point)] = bin_words[store_points.index(point)]

            elif entry["instr"].type == "VSTS" and (entry["instr"].vstart is None or entry["instr"].vend is None or entry["instr"].stride_size is None or entry["result"] is None):
                return False
            ######################
            count_bkwds = (count_bkwds - 1 + self.size) % self.size
        # input(f"mem dismabigresults:\n{dependency_results}")
        return dependency_results if dependency_results else True

    def splitbin(self, binary, instruction, conv_int=False, t=False):
        """splits binary into word size"""
        chunks = []
        chunksize = instruction.bitpack_size if not t else instruction
        for i in range(0, len(binary), chunksize):
            chunks.append(binary[i:i+chunksize])

        if conv_int:
            chunks = [int(chunk, 2) for chunk in chunks]
        return chunks
            
    def writeresult(self, instr, cpu):
        """for writeresult to update result"""

        if instr.type in {"ST", "STPI"}:
            # print(f"writting results ~~~~~~~~~~~~~~~~~~ {instr}, {instr.result}, {instr.effective_address}, {(instr.effective_address is not None and instr.result is not None)}")
            # done = 0 if not (instr.effective_address is not None and instr.result is not None) else 1
            done = 1 if (instr.effective_address is not None and instr.result is not None) else 0
            # if instr.result not filled then don't overwrite rob_entry["result"] with None as we want the phsyical register there so broadcasting can find it 
            if instr.result is None:
                fields = ["dst"]
                vals   = [instr.effective_address]
            else:
                fields = ["dst", "result", "done"]
                vals = [instr.effective_address, int(instr.result), done]
            self.ROB.loc[self.ROB["instr"] == instr, fields] = vals

        elif instr.type in {"VST", "VSTS"}:
            done = 1 if instr.result is not None else 0
            self.ROB.loc[self.ROB["instr"] == instr, ["dst", "result", "done"]] = [instr.effective_address, instr.result, 1]


        elif instr.type in {"BEQ", "BNE", "BLT", "BGT", "J", "B"}: # branches
            self.ROB.loc[self.ROB["instr"] == instr, "done"] = 1
            
        else: # other instrs
            self.ROB.loc[self.ROB["instr"] == instr, ["result", "done"]] = [instr.result, 1]

    def available(self):
        """checks if rob is available to accept entry"""
        return self.ROB.iloc[self.dispatch_pointer]["instr"] == None

    def add(self, instruction): # returns corresponding rob entry for dispatch
        """adds instructions to rob"""
        if instruction.type == "NOP":
            return True
        if self.available():
            
            # set up for broadcasting store value when read to rob entries
            result = None
            dst = "END"
            done = 0

            if instruction.type in {"ST", "STPI", "VST", "VSTS"}: # sets result to register so broad cast can find it and replace with value to write to memory
                result = instruction.operands[0]
                dst = None
                
            elif instruction.type != "HALT": # avoids setting HALT result
                dst = instruction.operands[0] if instruction.type not in {"BEQ", "BNE", "BLT", "BGT", "J", "B"} else None

            # set up rob entry
            self.ROB.iloc[self.dispatch_pointer] = {"instr"  : instruction,
                                                    "dst"    : dst,
                                                    "result" : result,
                                                    "done"   : done}
            
            rob_entry = f"rob{self.dispatch_pointer}"
            self.dispatch_pointer = (self.dispatch_pointer + 1) % self.size
            return rob_entry
        return False
    
    def __get_type(self, instr,):
        if instr is not None:
            return instr.type in {"ST", "STPI", "VST", "VSTS"}
        else:
            return False
        
    def __apply_result(self, instr, result):
        if instr is not None and instr.type == "ST":
            instr.result = int(result)
    
    def broadcast(self, reg, result, vec = False):
        """broadcasts result to stores that are waiting for a result to store"""
        # broadcasting values to be stored to mem for store instructions as store acts as store buffer
        # print("broadcasting")
        # print(reg, result)
        # print("broadcasting", result, "to", "reg", reg, vec)
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == reg), "instr"].apply(lambda instr: self.__apply_result(instr, result))
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == reg), "result"] = int(result) if not vec else result
        self.ROB.loc[(self.ROB["instr"].apply(self.__get_type)) & (self.ROB["result"] == result) & (self.ROB["dst"].str.contains("MEM")), "done"] = 1

    def flush(self):
        self.commit_pointer = 0
        self.dispatch_pointer = 0
        self.ROB = DataFrame({
            "instr"  : [None] * self.size, # type of operation
            "dst"    : [None] * self.size, # where result goes, can be physical register e.g. P1 or MEM location e.g. MEM1
            "result" : [None] * self.size, # value to write back
            "done"   : [None] * self.size, # indicates whether instruction is finished and results can be written to dst
        })
        self.ROB.index = [f"rob{n}" for n in range(self.size)]

    def flush_check(self, rob_entry, cpu):
        flushed = False
        if cpu.dynamic:
            state_change = 1 if rob_entry["instr"].branch_success else -1
            if (((cpu.BTB.take(rob_entry["instr"].pc) >= 0) and (not rob_entry["instr"].branch_success)) or # we took but branch shouldn't have been taken
                ((cpu.BTB.take(rob_entry["instr"].pc) < 0) and (rob_entry["instr"].branch_success))): # we didn't take but branch should have been taken
                self.flush()
                cpu.flush()
                flushed = True
                print("     >>>flushed<<<")
            else:
                cpu.RSB.popleft()
            cpu.BTB.update(pc=rob_entry["instr"].pc, state_change=state_change)

        elif not cpu.dynamic:
            # print("~~~~~~~~~~~~~~~~~",int(rob_entry["instr"].operands[2]), rob_entry["instr"].pc, rob_entry["instr"].branch_success)
            # print("~~~~~~~~~~~~~~~~~", int(rob_entry["instr"].operands[2]) > rob_entry["instr"].pc and rob_entry["instr"].branch_success and cpu.static_BRA_style == "STATIC")
            # print("~~~~~~~~~~~~~~~~~", int(rob_entry["instr"].operands[2]) < rob_entry["instr"].pc and not rob_entry["instr"].branch_success and cpu.static_BRA_style == "STATIC")

            
            if ((rob_entry["instr"].branch_success and cpu.static_BRA_style == "FIXED_never") or # we never take but was meant to
                (not rob_entry["instr"].branch_success and cpu.static_BRA_style == "FIXED_always") or
                (int(rob_entry["instr"].operands[2]) > rob_entry["instr"].pc and rob_entry["instr"].branch_success and cpu.static_BRA_style == "STATIC") or
                (int(rob_entry["instr"].operands[2]) < rob_entry["instr"].pc and not rob_entry["instr"].branch_success and cpu.static_BRA_style == "STATIC")):   # we always take but was meant to not take # FIXME static: if branching forwards was meant to happen flush
                self.flush()
                cpu.flush()
                flushed = True
                print("     >>>flushed<<<")
            else:
                cpu.RSB.popleft()
        return flushed

    def commit(self, cpu):
        """writes rob-entry instruction into registers and sets rob entry to none/empty """
        ret = False
        # print(cpu.RSB)

        for i in range(cpu.super_scaling):
            if self.ROB.iloc[self.commit_pointer]["instr"] and self.ROB.iloc[self.commit_pointer]["done"]:
                ##################### NOTE counting bypasses
                if self.ROB.iloc[self.commit_pointer]["instr"].bypassed_flag:
                    cpu.bypass_counter += 1
                    if self.ROB.iloc[self.commit_pointer]["instr"].type in {"BEQ", "BNE", "BLT", "BGT", "B", "J"}:
                        cpu.BRA_byp_counter += 1
                    elif self.ROB.iloc[self.commit_pointer]["instr"].type in {"ST", "LD", "LDI"}:
                        cpu.LSU_byp_counter += 1
                    else:
                        cpu.ALU_byp_counter += 1
                #####################

                # rob entry we're about to commit
                rob_entry = self.ROB.iloc[self.commit_pointer]
                print(f"Committed: {rob_entry["instr"]} dst:{rob_entry["dst"]} result:{rob_entry["result"]}")


                # if store write to memory else write to register
                if rob_entry["instr"].type == "ST": 
                    if rob_entry["result"] is not None:
                        cpu.MEM.write(rob_entry["dst"], rob_entry["result"])
                    else:
                        print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
                        break

                elif rob_entry["instr"].type == "STPI":
                    cpu.MEM.write(rob_entry["dst"], rob_entry["result"])
                    cpu.PRF.set_reg_val(reg=rob_entry["instr"].base_reg, value=int(rob_entry["instr"].effective_address[3:])) # write effective address to base register
                    
                    #handle rat stuff
                    cpu.r_freelist.remove(rob_entry["instr"].base_reg) # remove incoming physical register mapping from retirement freelist # NOTE not the same as freeing rat mapping

                    if cpu.rrat.loc[rob_entry["instr"].logical_operands[1], "Phys_reg"] is not None: #free up old physical register in retirement mapping
                        cpu.r_freelist.append(cpu.rrat.loc[rob_entry["instr"].logical_operands[1], "Phys_reg"]) # free physical register that was mapped to logical register (old)

                    # free physical register mapped to R2 
                    cpu.rat.free(cpu.rrat.loc[rob_entry["instr"].logical_operands[1], "Phys_reg"]) # free old physical register that was just mapped to a logical register that was just recommitted  i.e. can be free because nothing after will use that phys reg
                    cpu.rrat.loc[rob_entry["instr"].logical_operands[1], "Phys_reg"] = rob_entry["instr"].base_reg # update retirement logical to physical mapping of instr that just committed
                
                elif rob_entry["instr"].type == "LDPI":
                    cpu.PRF.set_reg_val(reg=rob_entry["instr"].base_reg, value=int(rob_entry["instr"].effective_address[3:])) # write effective address to base register
                    cpu.PRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])

                    logical_ops = [rob_entry["instr"].logical_operands[0], rob_entry["instr"].logical_operands[1]]
                    commit_physregs = [rob_entry["dst"], rob_entry["instr"].base_reg]

                    # handle rat stuff
                    for i in range(2):
                        cpu.r_freelist.remove(commit_physregs[i]) # remove incoming physical register mapping from retirement freelist # NOTE not the same as freeing rat mapping

                        if cpu.rrat.loc[logical_ops[i], "Phys_reg"] is not None: #free up old physical register in retirement mapping
                            cpu.r_freelist.append(cpu.rrat.loc[logical_ops[i], "Phys_reg"]) # free physical register that was mapped to logical register (old)

                        # free physical register mapped to R2 
                        cpu.rat.free(cpu.rrat.loc[logical_ops[i], "Phys_reg"]) # free old physical register that was just mapped to a logical register that was just recommitted  i.e. can be free because nothing after will use that phys reg
                        cpu.rrat.loc[logical_ops[i], "Phys_reg"] = commit_physregs[i] # update retirement logical to physical mapping of instr that just committed

                ##############
                elif rob_entry["instr"].type == "VST":
                    if rob_entry["instr"].result is not None:
                        cpu.MEM.v_write(vstart=rob_entry["instr"].vstart, vend=rob_entry["instr"].vend, int_list=self.splitbin(binary=rob_entry["instr"].result, instruction=rob_entry["instr"], conv_int=True))
                    else:
                        print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
                        break
                ##############
                elif rob_entry["instr"].type == "VSTS":
                    if rob_entry["instr"].result is not None:
                        cpu.MEM.v_write(vstart=rob_entry["instr"].vstart, vend=rob_entry["instr"].vend, int_list=self.splitbin(binary=rob_entry["instr"].result, instruction=rob_entry["instr"], conv_int=True),
                                        stride=True, stride_size=rob_entry["instr"].stride_size)
                    else:
                        print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
                        break
                
                elif rob_entry["instr"].type == "VLDS":
                    cpu.VRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])
                    cpu.vr_freelist.remove(rob_entry["dst"]) # remove incoming physical register mapping from retirement freelist # NOTE not the same as freeing rat mapping
                    cpu.vr_freelist.append(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free physical register that was mapped to logical register (old)
                    cpu.rat.free(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free old physical register that was just mapped to a logical register that was just recommitted  i.e. can be free because nothing after will use that phys reg
                    cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"] = rob_entry["dst"] # update retirement logical to physical mapping of instr that just committed
                ##############
                # if branch check if flush is needed
                elif rob_entry["instr"].type in {"BEQ", "BNE", "BLT", "BGT"}:
                    # if speculation is correct continue else flush
                    if cpu.bra_pred and self.flush_check(rob_entry=rob_entry, cpu=cpu):
                        print("returning flushed")
                        cpu.instructions += 1
                        cpu.flushed = True#todo maybe boost cycles by 10 as flush punishment
                        return True
                ##############
                elif rob_entry["instr"].type not in {"B", "J", "ST", "STPI", "LDPI"}: # arithmetic,load, etc instructions
                    if rob_entry["instr"].type[0] == "V":
                        cpu.VRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])
                        cpu.vr_freelist.remove(rob_entry["dst"]) # remove incoming physical register mapping from retirement freelist # NOTE not the same as freeing rat mapping
                    else:
                        cpu.PRF.set_reg_val(reg=rob_entry["dst"], value=rob_entry["result"])
                        # we remove currently in use physical register from r_freelist. This phys reg stays unfree until logical register is reused then the phys reg can be freed
                        cpu.r_freelist.remove(rob_entry["dst"]) # remove incoming physical register mapping from retirement freelist # NOTE not the same as freeing rat mapping
                    
                        # we add to retirement free list if mapping exists for Rx to Px i.e. rat mapping only replaced when new instruction commits to it
                    if cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"] is not None:
                        if rob_entry["instr"].type[0] == "V":
                            cpu.vr_freelist.append(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free physical register that was mapped to logical register (old)
                        else:
                            cpu.r_freelist.append(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free physical register that was mapped to logical register (old)

                    # free physical register that has been freed via new commit to logical register e.g. R1->P1 (P1 not free) R1->P2 commits and P1 can be freed
                    cpu.rat.free(cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"]) # free old physical register that was just mapped to a logical register that was just recommitted  i.e. can be free because nothing after will use that phys reg
                    cpu.rrat.loc[rob_entry["instr"].logical_operands[0], "Phys_reg"] = rob_entry["dst"] # update retirement logical to physical mapping of instr that just committed

                # clear rob entry
                self.ROB.iloc[self.commit_pointer] = {  "instr"    : None,
                                                        "dst"      : None,
                                                        "result"   : None,
                                                        "done"     : None,  }

                self.commit_pointer = (self.commit_pointer + 1) % self.size
                self.ROB = self.ROB.replace({np.nan:None})
                # cpu.VRF.rf = cpu.VRF.rf.replace({np.nan:None})
                cpu.instructions += 1
                ret = True
            else:
                print(f"Can't Commit : {self.ROB.iloc[self.commit_pointer]["instr"]}")
                break

        return ret
        
            


            