from assembler.assembler import assembler
from cpu_sim.Cpu import Cpu
from pipeline import *

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-pipelined", action="store_true")
parser.add_argument("-debug", action="store_true")
parser.add_argument("-step", action="store_true")
parser.add_argument("-f", default="pipe_test.asm")
parser.add_argument("-n_alu", default = 4, type=int)
parser.add_argument("-n_lsu", default = 1, type=int)
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

fetch_unit = FetchUnit.FetchUnit()
decode_unit = DecodeUnit.DecodeUnit(branch_label_map=branch_lines)
dispatch_unit = DispatchUnit.DispatchUnit()
issue_unit = IssueUnit.IssueUnit()
execute_units = []

execute_units.extend([ALU.ALU(ID=i) for i in range(args.n_alu)])
execute_units.extend([LSU.LSU(ID=i) for i in range(args.n_lsu)])


WriteResultUnit = WriteResultUnit.WriteResultUnit()

cpu = Cpu(instr_cache, fetch_unit, decode_unit, dispatch_unit, issue_unit, execute_units, WriteResultUnit)


cpu.run(debug=args.debug, step_toggle=args.step, pipelined=args.pipelined )