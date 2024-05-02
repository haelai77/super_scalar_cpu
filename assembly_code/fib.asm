# fib algo = https://www.geeksforgeeks.org/program-for-nth-fibonacci-number/#:~:text=%23%20Function%20for%20nth,0%20and%201


# R0 and R1 used for comparison to check end at input
LDI R1 1

# used for swapping adding a and b
LDI R2 0
LDI R3 1

######################### forloop ranges
# fib starting value
LDI R5 2

#>> INPUT <<# fib target n here we pick the 40th fib number
LDI R6 40
# 40th fib 102334155 
#########################

# checks if input is either 0 or 1
CHECKEND:
    ST R6 R0 R0
    BEQ R6 R0 END

    ST R6 R0 R0
    BEQ R6 R1 END
########### we do n + 1 for for loop
ADDI R6 R6 1

FIBSTEP:
    # c = a + b
    ADD R4 R2 R3

    # a = b (store b into MEM1 and load into a (R2))
    ST R3 R0 R0
    LD R2 R0 R0

    # b = c (STORE c into MEM1 and load into b (R3))
    ST R4 R0 R0
    LD R3 R0 R0
    # increase step
    ADDI R5 R5 1
    BNE R5 R6 FIBSTEP
    
END:
    HALT