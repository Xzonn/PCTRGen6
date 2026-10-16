import argparse
import os
import subprocess

import ips


GAMES = {
  "XY": {"X": "XY", "Y": "XY"},
  "ORAS": {"OR": "OR", "AS": "AS"},
}


def compile_helper(root: str, game: str, binary: bytes) -> bytes:
  for folder in sorted(os.listdir(f"{root}/{game}/code")):
    address = int(folder, 16)
    target = f"build/{game}/repl_{address:08X}"
    subprocess.run(
      [
        "make",
        f"TARGET={target}",
        f"BUILD=build/{game}/{folder}",
        f"SOURCES={game}/code/{folder}",
        f"SYMBOLS={game}/symbols.x",
        f"CODEADDR=0x{address:08X}",
      ],
      cwd=root,
      check=True,
    )
    with open(f"{root}/{target}.bin", "rb") as reader:
      patch = reader.read()
    # The input .code is decompressed; subtract the load address to get the file offset.
    offset = address - 0x00100000
    binary = binary[:offset] + patch + binary[offset + len(patch):]
  return binary


def compile_exefs_patch(game: str):
  for title, patch_game in GAMES[game].items():
    with open(f"original_files/exefs/{title}/code.bin", "rb") as reader:
      original = reader.read()
    binary = compile_helper("exefs_patch", patch_game, original)
    output = f"temp/output/exefs/{title}"
    os.makedirs(output, exist_ok=True)
    with open(f"{output}/code.bin", "wb") as writer:
      writer.write(binary)
    with open(f"{output}/code.ips", "wb") as writer:
      writer.write(bytes(ips.Patch.create(original, binary)))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("game", choices=GAMES)
  args = parser.parse_args()
  compile_exefs_patch(args.game)
