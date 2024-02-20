def asm_to_machine(assembly):
    '''converts a assembly into machine code'''
    instr_list: list[tuple] = []

    branch_lines = {}
    debug_lines = {}
    blank_lines = 0
    label_offset = 0

    for index, line in enumerate(assembly):
        if '#' in line:
            blank_lines += 1
            continue # skip comments

        instr = line.split() # split line into strings by whitespace

        if len(instr) == 1 and ":" in instr[0]: # if label is encountered
            branch_lines[str(instr[0][:-1])] = (index-1-label_offset-blank_lines, f"on line: {index+1}")
            label_offset += 1
            continue

        elif len(instr) == 0: # store number of blank lines for finding asm debugging later
            blank_lines += 1
            continue
        else:
            instr = (instr[0], instr[1:]) # (instr_typ: str, operands: str)

            debug_lines[(instr[0], index-blank_lines-label_offset)] = (f"{instr} on line: {index+1}")

        instr_list.append(instr)
    return instr_list, branch_lines, debug_lines

def assembler(file = "instr_cache.asm") -> tuple[tuple, ...]:
    '''returns machine code'''
    f = open(f"./assembly_code/{file}", "r")
    assembly = f.readlines()
    f.close()

    machine_code, branch_lines, debug_lines = asm_to_machine(assembly=assembly)
 
    return machine_code, branch_lines, debug_lines

