import json
import os

from helper import (
  DIR_TEXT,
  PATH_CHAR_COUNT_ORAS,
  PATH_CHAR_COUNT_ORAS_DEMO,
  PATH_CHAR_COUNT_XY,
  PATH_CHAR_TABLE_ORAS,
  PATH_CHAR_TABLE_ORAS_DEMO,
  PATH_CHAR_TABLE_XY,
)
from xzonn_mt_tools.helper import TranslationItem


def collect_characters(games: list[str] = ["XY"]) -> dict[str, int]:
  characters: dict[str, int] = {}
  for game in games:
    for root, dirs, files in os.walk(f"{DIR_TEXT}/{game}/zh_Hans"):
      for file in files:
        if not file.endswith(".json"):
          continue

        with open(os.path.join(root, file), "r", -1, "utf8") as reader:
          translations: list[TranslationItem] = json.load(reader)

        for item in translations:
          if item.get("trash", False):
            continue

          for char in item["translation"]:
            if 0x4E00 <= ord(char) <= 0x9FFF:
              characters[char] = characters.get(char, 0) + 1

  characters = dict(sorted(characters.items(), key=lambda x: x[1], reverse=True))

  return characters


if __name__ == "__main__":
  characters = collect_characters(["XY"])
  with open(PATH_CHAR_COUNT_XY, "w", -1, "utf8") as writer:
    json.dump(characters, writer, ensure_ascii=False, indent=2)

  with open(PATH_CHAR_TABLE_XY, "w", -1, "utf8") as writer:
    writer.write("".join(sorted(characters.keys())))
    writer.write("\n")

  characters = collect_characters(["ORAS"])
  with open(PATH_CHAR_COUNT_ORAS, "w", -1, "utf8") as writer:
    json.dump(characters, writer, ensure_ascii=False, indent=2)

  with open(PATH_CHAR_TABLE_ORAS, "w", -1, "utf8") as writer:
    writer.write("".join(sorted(characters.keys())))
    writer.write("\n")


  characters = collect_characters(["ORAS_Demo"])
  with open(PATH_CHAR_COUNT_ORAS_DEMO, "w", -1, "utf8") as writer:
    json.dump(characters, writer, ensure_ascii=False, indent=2)

  with open(PATH_CHAR_TABLE_ORAS_DEMO, "w", -1, "utf8") as writer:
    writer.write("".join(sorted(characters.keys())))
    writer.write("\n")
