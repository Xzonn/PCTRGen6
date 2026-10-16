import argparse
import json
import os
import shutil

from pyctr.type.tmd import TitleMetadataReader

TITLES = {
  "X": "0004000000055D00",
  "Y": "0004000000055E00",
  "OR": "000400000011C400",
  "AS": "000400000011C500",
}


def read_metadata(title: str, work: str):
  with open(f"{work}/title.tmd", "rb") as reader:
    tmd = TitleMetadataReader.load(reader)
  content = tmd.chunk_records[0]
  return {
    "title_id": tmd.title_id.upper(),
    "base_title_id": TITLES[title],
    "title_version": int(tmd.title_version),
    "content_index": content.cindex,
    "content_id": content.id,
  }


def patch_code(title: str, work: str):
  with open(f"temp/output/exefs/{title}/code.bin", "rb") as reader:
    binary = reader.read()
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


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("action", choices=["metadata", "code"])
  parser.add_argument("title", choices=TITLES)
  parser.add_argument("work")
  args = parser.parse_args()
  work = args.work.replace("\\", "/")
  if args.action == "metadata":
    print(json.dumps(read_metadata(args.title, work)), end="")
  else:
    patch_code(args.title, work)
