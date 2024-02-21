# FACTORIAL
# 10! = 3628800

START:
    LDI R1 10

    # counter 
    ST R1 0 R0
    LD R2 0 R0
    ADDI R2 R2 -1

    # end compare check
    LDI R3 1

MAIN:
    MUL R1 R1 R2
    ADDI R2 R2 -1
    BEQ R2 R3 END
    B MAIN

END:
    ST R1 0 R0
HALT
