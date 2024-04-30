# matrix multiplication (HADAMARD PRODUCT)
# answer = (30,36,42)(66,81,96)(102,126,150)

# set vector length to 3
LDI VLR 3 

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

########################
# matrix 2 row 1
LDI R10 1
LDI R11 2
LDI R12 3

# matrix 2 row 2
LDI R13 4
LDI R14 5
LDI R15 6

# matrix 2 row 3
LDI R16 7
LDI R17 8
LDI R18 9
########################

# memory pointer for storing data to load into vector
LDI R19 0
# memory offset
LDI R20 1

# rows into memory to load into vector regs
# store matrix 1 row 1
ST R1 R19 R0
STPI R2 R19 R20
STPI R3 R19 R20

# store matrix 1 row 2
STPI R4 R19 R20
STPI R5 R19 R20
STPI R6 R19 R20

# store matrix 1 row 3
STPI R7 R19 R20
STPI R8 R19 R20
STPI R9 R19 R20

# store matrix 2 row 1
STPI R10 R19 R20
STPI R11 R19 R20
STPI R12 R19 R20

# store matrix 2 row 2
STPI R13 R19 R20
STPI R14 R19 R20
STPI R15 R19 R20

# store matrix 2 row 3
STPI R16 R19 R20
STPI R17 R19 R20
STPI R18 R19 R20

######################### only 16 vector registers but we have renaming for 32

VLD.16 V1 R0
VLD.16 V2 R3
VLD.16 V3 R6

# load columns with load stride
VLDS.16 V4 R9 R3
VLDS.16 V5 R10 R3
VLDS.16 V6 R11 R3

######################## dot product vectors together
VDOT.16 V7 V1 V4
VDOT.16 V8 V1 V5
VDOT.16 V9 V1 V6

VDOT.16 V10 V2 V4
VDOT.16 V11 V2 V5
VDOT.16 V12 V2 V6

VDOT.16 V13 V3 V4
VDOT.16 V14 V3 V5
VDOT.16 V15 V3 V6

LDI VLR 1

ADDI R11 R0 21
VST.16 V7 R11

ADDI R11 R0 22
VST.16 V8 R11

ADDI R11 R0 23
VST.16 V9 R11

ADDI R11 R0 24
VST.16 V10 R11

ADDI R11 R0 25
VST.16 V11 R11

ADDI R11 R0 26
VST.16 V12 R11

ADDI R11 R0 27
VST.16 V13 R11

ADDI R11 R0 28
VST.16 V14 R11

ADDI R11 R0 29
VST.16 V15 R11

HALT