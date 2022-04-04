// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// while (true):
//     Read keyboard input
//     if input == 0: 
//         color = white
//         PAINT_SCREEN()
//     else: 
//         color = black
//         PAINT_SCREEN()
//
// void PAINT_SCREEN:
//     pixel = starting pixel pointer
//     while (pixel != keyboard input pointer):
//         *pixel = color
//         pixel++

(MAIN_LOOP)
    // Read keyboard input
    @KBD
    D = M

    // if input == 0: color = white
    @WHITE
    D; JEQ

    // else color = black
    @BLACK
    0; JMP

(WHITE)
    // color = white
    @color
    M = 0

    // Call paint screen function
    @PAINT_SCREEN
    0; JMP

(BLACK)
    // color = black
    @color
    M = -1

    // Call paint screen function
    @PAINT_SCREEN
    0; JMP

(PAINT_SCREEN)
    // pixel = SCREEN (starting pixel)
    @SCREEN
    D = A
    @pixel
    M = D

    // call PAINT_PIXEL_LOOP
    @PAINT_PIXEL_LOOP
    0; JMP

// while (pixel != KBD)
(PAINT_PIXEL_LOOP)
    // if pixel == KBD
    @pixel
    D = M
    @KBD
    D = D - A
    // break; (go back to while true loop start)
    @MAIN_LOOP
    D; JEQ

    // *pixel = color
    @color
    D = M
    @pixel
    A = M
    M = D

    // pixel++
    @pixel
    M = M + 1

    // get back to loop start
    @PAINT_PIXEL_LOOP
    0; JMP
