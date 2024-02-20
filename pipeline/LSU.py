class LSU:
    def __init__(self) -> None:
        pass

    def LD(self, instr, cpu):
        '''writes mem[baseAddr + offset] into resReg'''
        resAddr = instr.operands[0]
        offset = instr.operands[1] # immediate
        reg_base_val = cpu.RF.read(instr.operands[2]) # can just be zero

        mem_val = cpu.MEM.read(reg_base_val+offset)
        cpu.RF.write(resAddr, mem_val)

    def LDI(self, instr, cpu):
        ''' takes immediate and stores it into register specified in instruction'''
        resAddr = instr.operands[0]
        cpu.RF.write(resAddr, instr.operands[1])

    def ST(self, instr, cpu):
        '''memory[rf[r2] + offset] = rf[r1]
            args : r1, offset, r2'''
        
        val_in_reg = cpu.RF.read(instr.operands[0])
        offset = instr.operands[1]
        reg_base_val = cpu.RF.read(instr.operands[2]) # can just be zero

        cpu.MEM.write(reg_base_val + offset, val_in_reg)