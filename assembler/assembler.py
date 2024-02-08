from .mappings import opcodes
from collections import deque


def resolve_operand(operand) -> int:
    if  operand[0] in {'r', 'R'}:
        return int(operand[1])
    else:
        return int(operand)


def asm_to_machine(assembly) -> tuple[tuple, ...]:
    instr_list: list[tuple] = []

    for line in assembly:
        instr = line.split()

        if instr[0] not in opcodes: raise Exception("###### ERROR: opcode not in mapping / doesn't exist ######")

        instr = (opcodes[instr[0]], [resolve_operand(operand) for operand in instr[1:]])

        instr_list.append(instr)

    return tuple(instr_list)


def assembler(file = "./assembly_code/instr_cache.asm") -> tuple[tuple, ...]:
    f = open(file, "r")
    assembly = f.readlines()
    f.close()

    return asm_to_machine(assembly)

