from .Instruction import Instruction

class WritebackUnit:
    def __init__(self) -> None:
        pass
    
    # fixme: writeback should be in order :/ <<<<<<<<<<<<<<<<<<<<<<<<
    def writeback(self, cpu):
        '''writes results back to registers'''
        # selects finished instruction(s) to writeback  
        instructions = [instr for instr in cpu.INSTR_BUFF if type(instr) == Instruction and instr.done][:cpu.super_scaling] # hack currently only writes back 1 per superscaling 
        print(f"writing back: {instructions}")
        
        if len(instructions):
            for instr in instructions:
                if instr.result != None:
                    cpu.RF.write(instr.operands[0], instr.result)
            counter = 0
            new_buffer = []

            for instr in cpu.INSTR_BUFF:
                if type(instr) == Instruction:
                    if not instr.done or counter == cpu.super_scaling:
                        new_buffer.append(instr)
                    else:
                        counter += 1

            cpu.INSTR_BUFF = new_buffer # todo new buffer should also ignore store and branch instructions
            return True
        else:
            return False

        
 
