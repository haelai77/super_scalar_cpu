class LSU:
    def __init__(self) -> None:
        pass

    def LD(self, instr, cpu): 
        '''writes mem[baseAddr + offset] into resReg'''
        resAddr = instr.operands[0]
        mem_val = cpu.MEM.read(instr.operands[1])
        cpu.RF.write(resAddr, mem_val)

    def LDI(self, instr, cpu):
        ''' takes immediate and stores it into register specified in instruction'''
        resAddr = instr.operands[0]
        cpu.RF.write(resAddr, instr.operands[1])

    def ST(self, instr, cpu):
        '''memory[rf[r2] + rf[r3]] <- rf[r1]
           args : r1, offset, r2'''
        
        val_to_st = cpu.RF.read(instr.operands[0])
        address_in_mem = instr.operands[1]

        cpu.MEM.write(address_in_mem, val_to_st)