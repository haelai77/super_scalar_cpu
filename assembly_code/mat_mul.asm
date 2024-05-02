# matrix multiplication (squaring) (HADAMARD PRODUCT) # unrolled
# answer = (30,36,42)(66,81,96)(102,126,150)

########################
# matrix 1 row 1
LDI R1 1
LDI R2 2
LDI R3 3

# matrix 1 row 2
LDI R4 4
LDI R5 5
LDI R6 6

# matrix 1 row 3
LDI R7 7
LDI R8 8
LDI R9 9
################################################

# 1 1
MUL R20 R1 R1
MUL R21 R2 R4
MUL R22 R3 R7

# sum them together into R23
ADD R23 R20 R21
ADD R23 R22 R23
########################

# 1 2
MUL R20 R1 R2
MUL R21 R2 R5
MUL R22 R3 R8

# sum them together into R24
ADD R24 R20 R21
ADD R24 R22 R24
########################

# 1 3
MUL R20 R1 R3
MUL R21 R2 R6
MUL R22 R3 R9

# sum them together into R25
ADD R25 R20 R21
ADD R25 R22 R25
########################

# 2 1
MUL R20 R4 R1
MUL R21 R5 R4
MUL R22 R6 R7

# sum them together into R26
ADD R26 R20 R21
ADD R26 R22 R26
########################

# 2 2
MUL R20 R4 R2
MUL R21 R5 R5
MUL R22 R6 R8

# sum them together into R27
ADD R27 R20 R21
ADD R27 R22 R27
########################

# 2 3
MUL R20 R4 R3
MUL R21 R5 R6
MUL R22 R6 R9

# sum them together into R28
ADD R28 R20 R21
ADD R28 R22 R28
########################

# 3 1
MUL R20 R7 R1
MUL R21 R8 R4
MUL R22 R9 R7

# sum them together into R29
ADD R29 R20 R21
ADD R29 R22 R29
########################

# 3 2
MUL R20 R7 R2
MUL R21 R8 R5
MUL R22 R9 R8

# sum them together into R30
ADD R30 R20 R21
ADD R30 R22 R30
########################

# 3 3
MUL R20 R7 R3
MUL R21 R8 R6
MUL R22 R9 R9

# sum them together into R31
ADD R31 R20 R21
ADD R31 R22 R31
#######################
# store (23 24 25) (26 27 28) (29 30 31)
# answer = (30,36,42)(66,81,96)(102,126,150)

LDI R19 1
LDI R1 0

ST R23 R0 R0
STPI R24 R1 R19
STPI R25 R1 R19

STPI R26 R1 R19
STPI R27 R1 R19
STPI R28 R1 R19

STPI R29 R1 R19
STPI R30 R1 R19
STPI R31 R1 R19
HALT