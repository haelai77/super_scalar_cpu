# load values into R1 and R2
# store int div into R3
# store mul R2 R3 into R3
# store sub R1 - R3 into R3
    # if r1 mod r2 > 0
        # set a to b and b to remainder
        # branch to start 
    # else branch to end

# 1220 gcd 516 is 4
# 48 gcd 16 is 16
# 48 gcd 18 is 6
# 123215 gcd 235 is 5


START:
    # A
    LDI R1 123215
    # B
    LDI R2 235

MOD:
    DIV R3 R1 R2
    MUL R3 R2 R3
    SUB R3 R1 R3
    BEQ R3 0 END

    # STORE B
    ST R2 2 R0

    # STORE REMAINDER
    ST R3 3 R0

    # SET A TO B
    LD R1 2 R0

    # SET B TO REMAINDER
    LD R2 3 R0
    B MOD

    
END:
    ST R2 0 R0
HALT