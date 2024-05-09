LDI R1 1
LDI R2 2
LDI R3 3

# store 1 into MEM4
ST R1 R3 R3

# store R3 into MEM3 THEN write 3 into R1
STPI R3 R1 R2

# load (r1=3, r3=3) MEM6 into R5 and store 6 into R1
LDPI R5 R1 R3

# add 6 + 1 into r4
ADDI R4 R1 1

# Store R1=6 into MEM2
ST R1 R0 R2


# MEM4 = 1
# MEM3 = 3
# MEM2 = 6
# R1 = 1 -> 3 (STPI) -> 6 (LDPI)
# R4 = 7 (ADD R1=6 + 1)


HALT