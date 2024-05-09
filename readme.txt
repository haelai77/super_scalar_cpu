# aca
Super scalar pipelined processor simulator - Leo Lai

REQUIRES:
python 3.12.1
numpy 1.26.4
pandas 2.1.4
I recommend making a venv with e.g. miniconda found here: https://docs.anaconda.com/free/miniconda/miniconda-install

** example of flag usage at bottom
###############################################################
Flags:
-no_print              for no printing to terminal 
-rob_size [value]      for determining rob size (default 128)
-n_alu [value]         number of alus
-n_lsu [value]         number of lsu
-n_bra [value]         number of branch units
-rs_bypass             turns on reservation station bypassing
-f [path.asm]          determines assembly file you want to run
-bra_pred              turns on branch prediction
-dynamic               turns on dynamic branch prediction
-pipelined             turns on pipelining *** RUN WITH THIS IF NOT DOING SCALAR ***

-static_style [FIXED_never/FIXED_always/STATIC]  determines static branching style
-dyna_style [DYNAMIC_1bit/DYNAMIC_2bit]          determines dyanmic branching style

-ooo                   turns on out of order execution
-step [value]          allows you to do step by step execution, -1 skips to end, typing a value at each step jumps to that value. Can't jump backwards
-super_scaling [value] determines with of pipeline
###############################################################

To run a scalar version do "python main.py file.asm" 
To run a pipelined super scalar version do "python main.py -pipelined -f bubble_sort.asm -n_alu 4 -n_lsu 2 -n_bra 2 -bra_pred -static_style STATIC -dyna_style DYNAMIC_2bit -super_scaling 4 -rs_bypass -no_print"

(The default asm file run is bubble sort -> this takes a couple seconds)
Other options exist in /assembly_code: the main ones are GCD.asm, bubble_sort.asm, mat_mul.asm, mat_mul_v.asm, fib.asm, factorial.asm