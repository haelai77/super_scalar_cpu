from assembler.assembler import assembler
from cpu_sim.Cpu import Cpu
from pipeline import *
from execution_units import *

import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-pipelined", action="store_true")
parser.add_argument("-super_scaling", default=1, type=int)
parser.add_argument("-debug", action="store_true")
parser.add_argument("-step", default = -1, type=int)
parser.add_argument("-f", default="bubble_sort.asm")
parser.add_argument("-n_alu", default = 1, type=int)
parser.add_argument("-n_lsu", default = 1, type=int)
parser.add_argument("-n_bra", default = 1, type=int)
parser.add_argument("-dynamic", action="store_true")
parser.add_argument("-static_style", default="FIXED_always", type=str) # FIXED_never, STATIC (always take backwards branches never take forwards branches)
parser.add_argument("-dyna_style", default="DYNAMIC_2bit", type=str) # DYNAMIC_2bit

parser.add_argument("-bra_pred", action="store_true")
parser.add_argument("-ooo", action="store_true")
parser.add_argument("-rs_bypass", action="store_true")
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

fetch_unit = FetchUnit.FetchUnit(branch_label_map=branch_lines)
decode_unit = DecodeUnit.DecodeUnit()
dispatch_unit = DispatchUnit.DispatchUnit()
issue_unit = IssueUnit.IssueUnit()
execute_units = []

execute_units.extend([BRANCH.BRANCH(ID=i) for i in range(args.n_bra)])
execute_units.extend([LSU.LSU(ID=i) for i in range(args.n_lsu)])
execute_units.extend([ALU.ALU(ID=i) for i in range(args.n_alu)])



WriteResultUnit = WriteResultUnit.WriteResultUnit()

cpu = Cpu(instr_cache, fetch_unit, decode_unit, dispatch_unit, issue_unit, execute_units, WriteResultUnit,
          super_scaling=args.super_scaling, stat_style=args.static_style, dyna_style=args.dyna_style, dynamic=args.dynamic,
          bra_pred=args.bra_pred, ooo=args.ooo, rs_bypass=args.rs_bypass)


cpu.run(debug=args.debug, step_toggle=args.step, pipelined=args.pipelined )