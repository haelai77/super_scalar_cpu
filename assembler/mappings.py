# inspired by mips
opcodes = {
    #ALU ops
    "ADD" : 0x00, # (regs add) A <- B + C 
    "ADDI": 0x01, # (reg + const/immed) A <- B + const

    "SUB" : 0x02, # between regs ##### no subi because its just he same as adding a negative number (mips)

    "MUL" : 0x03, # between regs 
    "DIV" : 0x04, # between regs

    "CMP" : 0x05, # compare registers

    # load and store
    "LD"  : 0x06, # load from memory
    "LDC" : 0x07, # load constant into memory
    "ST"  : 0x08,

    # branch to immediate operand
    "BEQ" : 0X09, # branch on equal a == b
    "BNE" : 0X0A, # branch on not equal a != b
    "BLT" : 0X0B, # branch on less than a < b
    "BGT" : 0X0C, # BRANCH ON greater than a > b

    "J"   : 0x0D, # jump to addr in register
    "JI"  : 0x0E, # jump to immediate addr

    "HALT": 0x0F,
}
