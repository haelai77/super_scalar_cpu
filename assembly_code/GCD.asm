# load values into R1 and R2
# store int div into R3
# store mul R2 R3 into R3
# store sub R1 - R3 into R3
    # if r1 mod r2 > 0
        # set a to b and b to remainder
        # branch to start 
    # else branch to end

##############https://www.freecodecamp.org/news/euclidian-gcd-algorithm-greatest-common-divisor/

# 1220 gcd 516 is 4
# 48 gcd 16 is 16
# 48 gcd 18 is 6
# 123215 gcd 235 is 5

# ============================================

START:
    # A
    LDI R1 123215
    # B
    LDI R2 235

    LDI R4 2
    LDI R5 3

MOD:
    # a mod b = a - intdiv(a, b) * b
    DIV R3 R1 R2
    MUL R3 R2 R3
    SUB R3 R1 R3


    BEQ R3 R0 END

    # STORE B
    ST R2 R4 R0

    # STORE REMAINDER
    ST R3 R5 R0

    # SET A TO B
    LD R1 R4 R0

    # SET B TO REMAINDER
    LD R2 R5 R0
    B MOD

    
END:
    ST R2 R0 R0
HALT