def asm_to_machine(assembly) -> tuple[tuple, ...]:
    '''converts a assembly into machine code'''
    instr_list: list[tuple] = []

    for line in assembly:
        instr = line.split() # split line into strings by whitespace

        instr = (instr[0], instr[1:]) # (instr_typ: str, operands: str)

        instr_list.append(instr)

    return instr_list

def assembler(file = "instr_cache.asm") -> tuple[tuple, ...]:
    '''returns machine code'''
    f = open(f"./assembly_code/{file}", "r")
    assembly = f.readlines()
    f.close()

    return asm_to_machine(assembly)

