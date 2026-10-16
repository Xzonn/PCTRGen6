.syntax unified
.arch armv6k
.arm
.section .text,"ax",%progbits
.global Update_MountRomFS
.type Update_MountRomFS,%function
Update_MountRomFS:
    push {r0-r5,ip,lr}
    sub sp,sp,#8
    mov r2,#1
    mov r1,#0x10
    mov r0,#0x80
    bl Update_GetMountBufferSize
    mov r4,r0
    mov r0,#10
    bl Update_GetHeap
    mov r2,#4
    mov r1,r4
    bl Update_Allocate
    mov r3,r0
    mov r1,#1
    str r1,[sp,#4]
    mov r2,#0x10
    mov r1,#0x80
    ldr r0,=Update_MountName
    str r4,[sp]
    bl Update_MountArchive
    tst r0,#0x80000000
    beq mounted
    mov r2,#0
    mov r1,r2
    mov r0,r2
    bl Update_FatalError
mounted:
    add sp,sp,#8
    pop {r0-r5,ip,pc}
.size Update_MountRomFS,.-Update_MountRomFS
.pool
