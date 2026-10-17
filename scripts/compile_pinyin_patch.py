import argparse
import csv
import os
import struct
import subprocess
import sys

from elftools.elf.elffile import ELFFile
from helper import PATH_CHAR_TABLE_ORAS, PATH_CHAR_TABLE_XY

sys.path.insert(0, "bin/3DS-Decomp-Pipeline")
from ctrtype import CRO, BinaryReader, BinaryWriter, WritableBytes

GAMES = {
  "XY": {
    "titles": {"X": "XY", "Y": "XY"},
    "characters": PATH_CHAR_TABLE_XY,
    "hooks": "pinyin_keyboard/hooks_xy.s",
    "defines": [],
    "commit": 0x2DE8,
    "entries": [
      (0x5208, "Pinyin_Constructor"),
      (0x1464, "Pinyin_Action"),
      (0x22E8, "Pinyin_Refresh"),
    ],
    "heap": 0x625C,
    "allocation": 0x6270,
  },
  "ORAS": {
    "titles": {"OR": "OR", "AS": "AS"},
    "characters": PATH_CHAR_TABLE_ORAS,
    "hooks": "pinyin_keyboard/hooks_oras.s",
    "defines": ["-DPINYIN_ORAS"],
    "commit": 0x2F90,
    "entries": [
      (0x64E4, "Pinyin_Factory"),
      (0x1600, "Pinyin_Action"),
      (0x2540, "Pinyin_Refresh"),
    ],
    "heap": 0x6524,
    "allocation": 0x653C,
  },
}


def create_pinyin_table(characters_path: str, output: str):
  with open(characters_path, "r", -1, "utf8") as reader:
    characters = set(reader.read().strip())
  with open("files/pinyin.txt", "r", -1, "utf16") as reader:
    pinyin_table = dict(csv.reader(reader, delimiter=" "))
  entries = []
  candidates = []
  max_count = 0
  for pinyin, values in pinyin_table.items():
    values = [ord(character) for character in values if character in characters]
    if not values:
      continue
    code = 0
    for index, letter in enumerate(pinyin):
      code |= (ord(letter) - ord("a") + 1) << (25 - 5 * index)
    entries.append((code, len(candidates), len(values)))
    candidates.extend(values)
    max_count = max(max_count, len(values))
  entries.sort()
  candidate_offset = (0x10 + len(entries) * 8 + 0xF) & ~0xF
  with open(output, "wb") as writer:
    writer.write(struct.pack("<4I", len(entries), candidate_offset, max_count, 0))
    writer.writelines(struct.pack("<IHH", *entry) for entry in entries)
    writer.write(bytes(candidate_offset - 0x10 - len(entries) * 8))
    writer.writelines(struct.pack("<H", value) for value in candidates)


def expand_cro(binary: bytes, payload: bytes) -> bytes:
  cro = CRO.from_reader(BinaryReader("DllStrInput.cro", binary))
  extra = 0x6000
  boundary = cro.segment_table.obj[1].off
  original_text_size = cro.segment_table.obj[0].size
  visited = set()

  def move_object(value):
    if id(value) in visited:
      return
    visited.add(id(value))
    if isinstance(value, list):
      for item in value:
        move_object(item)
    elif hasattr(value, "__dict__"):
      if (
        hasattr(value, "off") and not hasattr(value, "index") and value.off >= boundary
      ):
        value.off += extra
      for item in vars(value).values():
        move_object(item)

  move_object(cro)
  cro.cro_size += extra
  cro.segment_table.obj[0].size = original_text_size + extra
  text_end = boundary - cro.text.off
  text = bytearray(cro.text.obj[:text_end] + bytes(extra) + cro.text.obj[text_end:])
  text[0x7000 - cro.text.off : 0x7000 - cro.text.off + len(payload)] = payload
  cro.text.obj = WritableBytes(text)
  cro.misc_info = cro.module_name.off.to_bytes(4, "little") + cro.misc_info[4:]
  writer = BinaryWriter()
  writer.write_bytes(binary[:boundary] + bytes(extra) + binary[boundary:])
  cro.write(writer)
  return writer.getvalue()


def compile_pinyin_patch(game: str):
  config = GAMES[game]
  root = f"temp/pinyin_keyboard/{game}"
  os.makedirs(root, exist_ok=True)
  create_pinyin_table(config["characters"], f"{root}/table.bin")
  prefix = f"{os.environ['DEVKITARM']}/bin/arm-none-eabi-"
  subprocess.run(
    [
      f"{prefix}gcc",
      "-marm",
      "-march=armv6k",
      "-mtune=mpcore",
      "-Os",
      "-ffreestanding",
      "-fno-builtin",
      "-fno-unwind-tables",
      "-fno-jump-tables",
      "-nostdlib",
      *config["defines"],
      "-Wl,-Ttext=0x7000",
      f"-Wl,--defsym,Native_Commit=0x{config['commit']:x}",
      "-Wl,-e,Pinyin_Action",
      f"-Wl,-Map={root}/keyboard.map",
      "pinyin_keyboard/native_pinyin.c",
      config["hooks"],
      "-o",
      f"{root}/keyboard.elf",
    ],
    check=True,
  )
  subprocess.run(
    [
      f"{prefix}objcopy",
      "-O",
      "binary",
      f"{root}/keyboard.elf",
      f"{root}/keyboard.bin",
    ],
    check=True,
  )
  with open(f"{root}/keyboard.elf", "rb") as reader:
    elf = ELFFile(reader)
    symbols = {
      symbol.name: symbol.entry.st_value
      for symbol in elf.get_section_by_name(".symtab").iter_symbols()
    }
  with open(f"{root}/keyboard.bin", "rb") as reader:
    payload = reader.read()
  assert len(payload) <= 0x5800
  for title, source in config["titles"].items():
    with open(f"original_files/romfs/{source}/DllStrInput.cro", "rb") as reader:
      patched = bytearray(reader.read())
    for offset, symbol in config["entries"]:
      branch = 0xEA000000 | (((symbols[symbol] - offset - 8) // 4) & 0xFFFFFF)
      patched[offset : offset + 4] = branch.to_bytes(4, "little")
    offset = config["heap"]
    patched[offset : offset + 4] = bytes.fromhex("022aa0e3")
    offset = config["allocation"]
    patched[offset : offset + 4] = bytes.fromhex("020ba0e3")
    binary = expand_cro(bytes(patched), payload)
    output = f"temp/output/romfs/{title}"
    os.makedirs(output, exist_ok=True)
    with open(f"{output}/DllStrInput.cro", "wb") as writer:
      writer.write(binary)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("game", choices=GAMES)
  args = parser.parse_args()
  compile_pinyin_patch(args.game)
