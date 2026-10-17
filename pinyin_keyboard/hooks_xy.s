.syntax unified
.arm
.section .text
.global Original_Constructor, Original_Action, Original_Refresh, Pinyin_GetTable
Original_Constructor:
    .incbin "original_files/romfs/XY/DllStrInput.cro", 0x5208, 4
    b 0x520c
Original_Action:
    .incbin "original_files/romfs/XY/DllStrInput.cro", 0x1464, 4
    b 0x1468
Original_Refresh:
    .incbin "original_files/romfs/XY/DllStrInput.cro", 0x22e8, 4
    b 0x22ec
Pinyin_GetTable:
    adr r0, PinyinTable
    bx lr
.align 4
PinyinTable:
    .incbin "temp/pinyin_keyboard/XY/table.bin"
