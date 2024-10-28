
## Super scalar pipelined processor simulator - Leo Lai<br />

REQUIRES:<br />
python 3.12.1<br />
numpy 1.26.4<br />
pandas 2.1.4<br />
I recommend making a venv with e.g. miniconda found here: https://docs.anaconda.com/free/miniconda/miniconda-install/<br />


Flags:<br />
**\-no_print** for no printing to terminal <br />
**\-rob_size [value]**      for determining rob size (default 128)<br />
**\-n_alu [value]**         number of alus<br />
**\-n_lsu [value]**         number of lsu<br />
**\-n_bra [value]**         number of branch units<br />
**\-rs_bypass**             turns on reservation station bypassing<br />
**\-f [path.asm]**          determines assembly file you want to run<br />
**\-bra_pred**              turns on branch prediction<br />
**\-dynamic**               turns on dynamic branch prediction<br />
**\-static_style [FIXED_never/FIXED_always/STATIC]** <br /> determines static branching style
**\-dyna_style [DYNAMIC_1bit/DYNAMIC_2bit]**<br /> determines dyanmic branching style
**\-ooo**                   turns on out of order execution<br />
**\-step [value]**          allows you to do step by step execution, -1 skips to end, typing a value at each step jumps to that value. Can't jump backwards<br />
**\-super_scaling [value]** determines with of pipeline<br />

To run a scalar version do "python main.py file.asm" <br />
To run a pipelined super scalar version do "python main.py -f bubble_sort.asm -n_alu 4 -n_lsu 2 -n_bra 2 -bra_pred -static_style STATIC -dyna_style DYNAMIC_2bit -super_scaling 4 -rs_bypass -no_print"<br />


The default asm file run is bubble sort. <br />
Other options exist in /assembly_code <br />
