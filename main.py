from assembler.assembler import assembler
from cpu_sim.Cpu import Cpu
from pipeline import *
import sys

assembly_file = sys.argv[1] if len(sys.argv)>1 else "instr_cache.asm"

instr_cache = assembler(file=assembly_file)

if len(instr_cache) == 0:
    raise Exception(f"{assembly_file} is empty")
# print(*instr_cache, sep="\n")

fetch_unit = FetchUnit.FetchUnit()
decode_unit = DecodeUnit.DecodeUnit()
execute_unit = ExecuteUnit.ExecuteUnit()
writeback_unit = WritebackUnit.WritebackUnit()

cpu = Cpu(instr_cache, fetch_unit, decode_unit, execute_unit, writeback_unit)

cpu.run()