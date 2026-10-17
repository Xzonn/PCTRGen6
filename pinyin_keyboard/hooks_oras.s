.syntax unified
.arm
.section .text
.global Original_Factory, Original_Action, Original_Refresh, Pinyin_GetTable
Original_Factory:
    .incbin "original_files/romfs/OR/DllStrInput.cro", 0x64e4, 4
    b 0x64e8
Original_Action:
    .incbin "original_files/romfs/OR/DllStrInput.cro", 0x1600, 4
    b 0x1604
Original_Refresh:
    .incbin "original_files/romfs/OR/DllStrInput.cro", 0x2540, 4
    b 0x2544
Pinyin_GetTable:
    adr r0, PinyinTable
    bx lr
.align 4
PinyinTable:
    .incbin "temp/pinyin_keyboard/ORAS/table.bin"
