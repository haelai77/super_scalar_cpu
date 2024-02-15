from .Instruction import Instruction

class WritebackUnit:
    def __init__(self) -> None:
        pass
    
    def writeback(self, cpu):
        '''writes results back to registers'''
        instr: Instruction = cpu.INSTR_BUFF.popleft()

        try:
            if instr.result != None:
                cpu.RF.write(instr.operands[0], instr.result)
        except:
            raise Exception(f"writeback failed \n Instruction_type:{instr.type} \n Instrcution_ops:{instr.operands} \n Instruction_res:{instr.result}")
