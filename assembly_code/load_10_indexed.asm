# mem pointer
    LDI R3 0

# number of checks
    LDI R5 9
    
# success counters
    LDI R6 0 

# end of list
    LDI R7 10

# load testing list into memory
    LDI R1 10
    LDI R2 0

# store first spot
    ST R1 R0 R0

# load 1 into r4 to add to STPI
    LDI R4 1

# fill memory with 9 -> 1 at mem index 1 to 9
NEXT:
    # next list item to store
    ADDI R1 R1 -1

    # store list item into mem
    STPI R1 R3 R4

    # branch if not done
    BNE R1 R2 NEXT
    HALT
    #########################################################################################
    B START_SORTING
# ================================================

SWAP_CHECK:   
    # LOAD MEM LOCATION AT 2 POINTERS INTO R3 AND R4
    LD R3 R0 R1
    LD R4 R0 R2

    # swap if unsorted and set counter back to zero for number of checks required to end
    BGT R3 R4 RESET_COUNTER_&_SWAP

    # else if ordered increase check by 1
    ADDI R6 R6 1
    B CONTINUE

RESET_COUNTER_&_SWAP:
    LDI R6 0
    
    # swap values
    ST R4 R0 R1
    ST R3 R0 R2
    B CONTINUE

INIT_POINTERS:
    LDI R1 0
    LDI R2 1
    B MAIN_LOOP

# =================================================
START_SORTING:
    # initialise swap pointers
    LDI R1 0
    LDI R2 1

    MAIN_LOOP:
        BEQ R5 R6 END
        BEQ R2 R7 INIT_POINTERS
        B SWAP_CHECK
        
        CONTINUE:
            ADDI R1 R1 1
            ADDI R2 R2 1
            B MAIN_LOOP
END:
    HALT