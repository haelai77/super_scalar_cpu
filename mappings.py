# inspired by mips
opcodes = {
    #ALU ops
    "ADD" : 0x00, # r1 <- r2 + r3
    "ADDI": 0x01, # r1 <- r2 + immediate

    "SUB" : 0x02, # r1 <- r2 - r3
    # no subi because addi can just add a negative number

    "MUL" : 0x03, # r1 <- r2 * r3
    "DIV" : 0x04, # r1 <- r2 // r3 

    "CMP" : 0x05, # r1 <- r2 CMP r3 compare registers r2,r3 st in r1 args : r1 r2 r3

    # load and store
    "LD"  : 0x06, # r1 <- memory[regs[R2] + regs[R3]] args: r1, r2, r3 # todo needs to be r1, r2 r4 where r1 <- mem[regs[r2] + regs[r3]]
    "LDI" : 0x07, # r1 <- immediate args: r1, immediate
    "ST"  : 0x08, # r1 -> memory[regs[R2] + regs[R3]]  args:  R1, R2, R3 # todo should be indexed as well 
    "STI" : "??", # immediate -> memory[regs[R2] + regs[R3]]  args:  R1, R2, R3 # todo should be indexed as well 

    "LDPI": "??", # r1 <- mem[r2+r3] and r2 <- r2 + r3 # pre indexed
    "STPI": "??", # r1 -> mem[r2+r3] and r2 <- r2 + r3

    "VADD": "??", # v1 <- v2 + v3 # add vectors # we will specify bit packing size i.e. #SIMD_lanes = #regbits / size, where size can be 8, 16 or 32 ( 255 -> 8bit max, 65,535 ->  16bit max )
    "VSUB": "??", # v1 <- v2 - v3 # add vectors 
    "VMUL": "??", # v1 <- v2 * v3 # add vectors 
    "VDOT": "??", # v1 <- v2 DOT v3 # add vectors 

    # how far this goes depends on the number of bits specified
    "VLD": "??", # v1, r1 LOAD into v1 from mem starting at r1 address in mem  
    "VST": "??", # v1, r1 STORE into v1 from mem starting at r1 address in mem 

    # R1 is start pointer for vector and R2 is stride length
    "VLDS": "??", # v1, r1, r2 LOAD into v1 from mem starting at r1 address and then subsequent strides r2
    "VSTS": "??", # v1, r1, r2 STORE into v1 from mem starting at r1 address and then subsequent strides r2

    # branch to immediate operand (COMPARISON BETWEEN REGISTERS)
    "BEQ" : 0X09, # branch on equal a == b,       args: r1 r2 LABEL
    "BNE" : 0X0A, # branch on not equal a != b,   args: r1 r2 LABEL
    "BLT" : 0X0B, # branch on less than a < b,    args: r1 r2 LABEL
    "BGT" : 0X0C, # BRANCH ON greater than a > b, args: r1 r2 LABEL

    "J"   : 0x0D, # relative branch based on immediate passed in pc += (immediate) args : immediate
    "B"   : 0x0E, # jump to immediate addr

    "HALT": 0x0F,
}
