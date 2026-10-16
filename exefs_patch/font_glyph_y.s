.syntax unified
.arch armv6k
.arm
.section .text,"ax",%progbits
.global Font_AdjustGlyphY
.type Font_AdjustGlyphY,%function
Font_AdjustGlyphY:
    /* r4 points to TGLP; r0 contains the row index multiplied by the cell pitch. */
    /* Select the large font with 19 rows and no top margin. */
    ldrb ip,[r4,#1]
    cmp ip,#26
    bne original_y
    ldrh ip,[r4,#0xe]
    cmp ip,#19
    bne original_y
    ldr ip,=Font_Manager
    ldr ip,[ip]
    ldr ip,[ip,#0x10]
    ldr ip,[ip,#8]
    ldr ip,[ip,#8]
    cmp ip,r4
    bxeq lr
original_y:
    add r0,r0,#1
    bx lr
.size Font_AdjustGlyphY,.-Font_AdjustGlyphY
.pool
