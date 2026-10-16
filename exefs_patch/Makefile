.SUFFIXES:

ifeq ($(strip $(DEVKITARM)),)
$(error Please set DEVKITARM to the devkitARM directory)
endif

PREFIX := $(DEVKITARM)/bin/arm-none-eabi-
CC := $(PREFIX)gcc
LD := $(PREFIX)ld
OBJCOPY := $(PREFIX)objcopy
OBJDUMP := $(PREFIX)objdump

TARGET ?= newcode
BUILD ?= build
SOURCES ?= source
SYMBOLS ?= symbols.x
ARCH := -mabi=aapcs -march=armv6k -mtune=mpcore -marm
ASFLAGS := -g $(ARCH) -I.
SFILES := $(notdir $(wildcard $(SOURCES)/*.s))
OFILES := $(addprefix $(BUILD)/,$(SFILES:.s=.o))
VPATH := $(SOURCES)

.PHONY: all
all: $(TARGET).bin $(TARGET).sym

$(BUILD):
	mkdir -p $@

$(BUILD)/%.o: %.s font_glyph_y.s | $(BUILD)
	$(CC) -x assembler-with-cpp $(ASFLAGS) -c $< -o $@

$(TARGET).elf: $(OFILES) $(SYMBOLS) linker.x
	$(LD) -T $(SYMBOLS) -T linker.x -Ttext $(CODEADDR) -Map $(TARGET).map $(OFILES) -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(TARGET).sym: $(TARGET).elf
	$(OBJDUMP) -t $< > $@
