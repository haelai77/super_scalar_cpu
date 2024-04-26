# mem pointer
    LDI R3 0

# load testing list into memory (bounds)
    LDI R1 10
    LDI R2 0

# store first spot
    ST R1 R0 R0

# load 1 into r4 to add to STPI
    LDI R4 1

NEXT:
    # next list item to store
    ADDI R1 R1 -1

    # store list item into mem
    STPI R1 R3 R4

    # branch if not done
    BNE R1 R2 NEXT


LDI R13 0
LDI R14 1
LD R1 R13 R0
LDPI R2 R13 R14
LDPI R3 R13 R14
LDPI R4 R13 R14
LDPI R5 R13 R14
LDPI R6 R13 R14
LDPI R7 R13 R14
LDPI R8 R13 R14
LDPI R9 R13 R14
LDPI R10 R13 R14
HALT