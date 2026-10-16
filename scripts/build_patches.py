import argparse
import glob
import os
import shutil
import subprocess
import tempfile

from pyctr.type.tmd import TitleMetadataReader

GAMES = {
  "XY": {"X": "0004000000055D00", "Y": "0004000000055E00"},
  "ORAS": {"OR": "000400000011C400", "AS": "000400000011C500"},
}
CTRTOOL = "bin/Project_CTR/ctrtool.exe"
MAKEROM = "bin/Project_CTR/makerom.exe"
THREEDSTOOL = "bin/3dstool/3dstool.exe"


def copy_files(source: str, destination: str):
  for root, folders, files in os.walk(source):
    relative = os.path.relpath(root, source).replace("\\", "/")
    os.makedirs(f"{destination}/{relative}", exist_ok=True)
    for name in files:
      shutil.copyfile(f"{root}/{name}", f"{destination}/{relative}/{name}")


def build_patches(game: str, title: str, title_id: str):
  os.makedirs("temp/build_patches", exist_ok=True)
  work = tempfile.mkdtemp(prefix=f"{title}_", dir="temp/build_patches").replace("\\", "/")
  subprocess.run(
    [CTRTOOL, "--quiet", f"--contents={work}/content", f"--tmd={work}/title.tmd", f"original_files/updates/{title}.cia"],
    check=True,
  )
  with open(f"{work}/title.tmd", "rb") as reader:
    tmd = TitleMetadataReader.load(reader)
  content = tmd.chunk_records[0]
  subprocess.run(
    [
      THREEDSTOOL, "-x", "-t", "cxi", "-f", f"{work}/content.{content.cindex:04x}.{content.id}",
      "--header", f"{work}/header.bin", "--exh", f"{work}/exheader.bin",
      "--logo", f"{work}/logo.bin", "--plain", f"{work}/plain.bin",
      "--exefs", f"{work}/exefs.bin", "--romfs", f"{work}/romfs.bin",
    ],
    check=True,
  )
  subprocess.run(
    [THREEDSTOOL, "-x", "-t", "exefs", "-f", f"{work}/exefs.bin", "--header", f"{work}/exefs_header.bin", "--exefs-dir", f"{work}/exefs"],
    check=True,
  )
  subprocess.run(
    [THREEDSTOOL, "-x", "-t", "romfs", "-f", f"{work}/romfs.bin", "--romfs-dir", f"{work}/romfs"],
    check=True,
  )

  luma = f"out/luma/titles/{title_id}"
  source_game = "AS" if title == "AS" else game
  for source in sorted(glob.glob(f"original_files/chinese/{source_game}/a/a*.garc")):
    digits = os.path.basename(source)[1:4]
    destination = f"{luma}/romfs/a/{'/'.join(digits)}"
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    shutil.copyfile(source, destination)
  copy_files(f"temp/output/japanese/{game}", f"{luma}/romfs")
  shutil.copyfile(f"temp/output/exefs/{title}/code.ips", f"{luma}/code.ips")

  with open(f"temp/output/exefs/{title}/code.bin", "rb") as reader:
    binary = reader.read()
  copy_files(f"{luma}/romfs", f"{work}/romfs")
  for root, folders, files in os.walk(f"{work}/romfs/a", topdown=False):
    for name in files:
      path = os.path.relpath(f"{root}/{name}", f"{work}/romfs").replace("\\", "/")
      original_path = (f"rom:/{path}\0").encode("utf-16le")
      if original_path not in binary:
        original_path = (f"rom2:/{path}\0").encode("utf-16le")
        binary.index(original_path)
      path = f"a/{path[2:].replace('/', '')}"
      update_path = (f"rom2:/{path}\0").encode("utf-16le")
      binary = binary.replace(original_path, update_path.ljust(len(original_path), b"\0"))
      shutil.move(f"{root}/{name}", f"{work}/romfs/{path}")
    if root != f"{work}/romfs/a":
      os.rmdir(root)
  with open(f"{work}/code.bin", "wb") as writer:
    writer.write(binary)
  subprocess.run(
    [THREEDSTOOL, "-z", "-f", f"{work}/code.bin", "--compress-type", "blz", "--compress-out", f"{work}/exefs/code.bin"],
    check=True,
  )
  subprocess.run(
    [THREEDSTOOL, "-c", "-t", "exefs", "-f", f"{work}/translated_exefs.bin", "--header", f"{work}/exefs_header.bin", "--exefs-dir", f"{work}/exefs"],
    check=True,
  )
  subprocess.run(
    [THREEDSTOOL, "-c", "-t", "romfs", "-f", f"{work}/translated_romfs.bin", "--romfs-dir", f"{work}/romfs"],
    check=True,
  )
  subprocess.run(
    [
      THREEDSTOOL, "-c", "-t", "cxi", "-f", f"{work}/translated.cxi", "--not-encrypt",
      "--header", f"{work}/header.bin", "--exh", f"{work}/exheader.bin",
      "--logo", f"{work}/logo.bin", "--plain", f"{work}/plain.bin",
      "--exefs", f"{work}/translated_exefs.bin", "--romfs", f"{work}/translated_romfs.bin",
    ],
    check=True,
  )
  os.makedirs("out/cia", exist_ok=True)
  subprocess.run(
    [
      MAKEROM, "-f", "cia", "-o", f"out/cia/{tmd.title_id.upper()}.cia",
      "-content", f"{work}/translated.cxi:{content.cindex}:0x{content.id}",
      "-ver", str(int(tmd.title_version)), "-ignoresign",
    ],
    check=True,
  )


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("game", choices=GAMES)
  args = parser.parse_args()
  for title, title_id in GAMES[args.game].items():
    build_patches(args.game, title, title_id)
