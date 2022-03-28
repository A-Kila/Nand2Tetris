// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// R2 = 0
// while (R0 != 0)
//     R2 += R1
//     R0--

// while loop start
// R2 = 0
@2
M = 0
(LOOP)
    // if (R0 == 0) break the loop
    @0
    D = M
    @END
    D; JEQ

    // R2 += R1
    @1
    D = M
    @2
    M = M + D

    // R0--
    @0
    M = M - 1
    
    // jump while loop start
    @LOOP
    0; JMP

(END)
    @END
    0; JMP
