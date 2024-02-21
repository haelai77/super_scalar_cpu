from assembler.assembler import assembler
from cpu_sim.Cpu import Cpu
from pipeline import *
import sys

assembly_file = sys.argv[1] if len(sys.argv)>1 else "bubble_sort.asm"

instr_cache, branch_lines, debug_lines = assembler(file=assembly_file)


if len(instr_cache) == 0:
    raise Exception(f"{assembly_file} is empty")

# print(*instr_cache, sep="\n")
print("################ debug_lines")
for key, value in debug_lines.items():
    print(key, value)
print("################  branch_lines")
for key, value in branch_lines.items():
    print(key, value)
print("################")

fetch_unit = FetchUnit.FetchUnit(debug_lines)
decode_unit = DecodeUnit.DecodeUnit(branch_label_map=branch_lines)
execute_unit = ExecuteUnit.ExecuteUnit()
writeback_unit = WritebackUnit.WritebackUnit()

cpu = Cpu(instr_cache, fetch_unit, decode_unit, execute_unit, writeback_unit)


cpu.run(debug=True)