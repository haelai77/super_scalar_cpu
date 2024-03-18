from assembler.assembler import assembler
from cpu_sim.Cpu import Cpu
from pipeline import *
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-pipelined", action="store_true")
parser.add_argument("-debug", action="store_true")
parser.add_argument("-f", default="bubble_sort.asm")
parser.add_argument("-n_exec", default = 1)
args = parser.parse_args()


instr_cache, branch_lines, debug_lines = assembler(file=args.f)

if len(instr_cache) == 0:
    raise Exception(f"{args.f} is empty")

# print(*instr_cache, sep="\n")
print(f"################ debug_lines {args.f}")
for key, value in debug_lines.items():
    print(key, value)
print("################  branch_lines")
for key, value in branch_lines.items():
    print(key, value)
print("################")

fetch_unit = FetchUnit.FetchUnit(debug_lines)
decode_unit = DecodeUnit.DecodeUnit(branch_label_map=branch_lines)
execute_units = [ExecuteUnit.ExecuteUnit()] * args.n_exec
writeback_unit = WritebackUnit.WritebackUnit()

cpu = Cpu(instr_cache, fetch_unit, decode_unit, execute_units, writeback_unit)


cpu.run(debug=args.debug, pipelined=args.pipelined )