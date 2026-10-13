import os
import shutil

from bcfnt import BCFNT, CWDHInfo
from font_helper import image_to_sheet, sheet_to_image
from helper import (
  CHINESE_PUNCTUATIONS_CENTER,
  CHINESE_PUNCTUATIONS_LEFT,
  CHINESE_PUNCTUATIONS_RIGHT,
  PATH_CHAR_TABLE_ORAS,
  PATH_CHAR_TABLE_ORAS_DEMO,
  PATH_CHAR_TABLE_XY,
  PATH_GARC_FONT_ORAS,
  PATH_GARC_FONT_ORAS_DEMO,
  PATH_GARC_FONT_XY,
)
from PIL import Image, ImageChops
from windows_gdi import GdiFont, Glyph


class IDrawConfg:
  n_width: int
  n_height: int
  n_cell_width: int
  n_cell_height: int
  n_baseline: int

  def __init__(self, char_table: dict[str, str] = {}):
    self.char_table: dict[str, str] = char_table

  def get_new_chars(self, old_char_map: dict[int, int]) -> list[str]:
    n_characters = []
    for char_code in old_char_map.values():
      char = chr(char_code)
      if char in "\n[]":
        continue

      if 0x80 <= char_code <= 0x303F:
        if char not in "×áéíóú—―‘’“”…◆●★☆♀♂\u2600\u2601\u2602\u2603　、。《》「」":
          continue

      if 0x30FD <= char_code <= 0x4DFF:
        continue

      if 0x4E00 <= char_code <= 0x9FFF:
        # 汉字
        continue

      if 0xAC00 <= char_code <= 0xD7AF:
        # 韩文
        continue

      if 0xFF5F <= char_code <= 0xFF9F:
        # 半角假名
        continue

      n_characters.append(char)

    for k, v in self.char_table.items():
      if k not in n_characters:
        n_characters.append(k)

    return sorted(n_characters)

  def needs_redraw(self, char: str) -> bool:
    if 0x4E00 <= ord(char) <= 0x9FFF:
      return True

    if char in CHINESE_PUNCTUATIONS_LEFT:
      return True
    elif char in CHINESE_PUNCTUATIONS_CENTER:
      return True
    elif char in CHINESE_PUNCTUATIONS_RIGHT:
      return True

    elif "０" <= char <= "９":
      return True
    elif "Ａ" <= char <= "Ｚ":
      return True
    elif "ａ" <= char <= "ｚ":
      return True

    return False

  def draw(self, char: str) -> tuple[Image.Image, CWDHInfo]:
    raise NotImplementedError("This method should be implemented by subclasses.")

  def draw_glyph(self, char: str) -> Glyph:
    raise NotImplementedError("This method should be implemented by subclasses.")

  def draw_high_res(self, char: str, glyph: Glyph) -> Glyph:
    return glyph.resize(8)

  def close(self):
    raise NotImplementedError("This method should be implemented by subclasses.")


class DrawConfig1(IDrawConfg):
  n_width = 256
  n_height = 512
  n_cell_width = 25
  n_cell_height = 27
  n_baseline = 21

  def __init__(self, char_table: dict[str, str] = {}):
    super().__init__(char_table)
    char_table["・"] = "·"
    self.font = GdiFont("files/fonts/FZY4K.ttf", "方正粗圆_GBK", 24)
    self.font_high_res = GdiFont("files/fonts/FZY4K.ttf", "方正粗圆_GBK", 24 * 8)
    self.font_japanese = GdiFont("files/fonts/FOT-RodinNTLGPro-DB.otf", "FOT-RodinNTLG Pro DB", 24 * 8)

  def draw(self, char: str) -> tuple[Image.Image, CWDHInfo]:
    glyph = self.draw_glyph(char)
    image = Image.new("RGBA", (self.n_cell_width, self.n_cell_height))
    image.paste(glyph.image, (0, self.n_baseline - glyph.ascent))
    return image, CWDHInfo(glyph.left, glyph.image.width, glyph.advance)

  def draw_glyph(self, char: str) -> Glyph:
    glyph = self.font.draw(self.char_table.get(char, char), 4)
    glyph.advance = 24
    return glyph

  def draw_high_res(self, char: str, glyph: Glyph) -> Glyph:
    if 0xE000 <= ord(char) < 0xF000:
      return glyph.resize(8)
    draw_char = self.char_table.get(char, char)
    font = self.font_high_res if self.needs_redraw(char) else self.font_japanese
    return font.draw(draw_char)

  def close(self):
    self.font.close()
    self.font_high_res.close()
    self.font_japanese.close()


class DrawConfig2(IDrawConfg):
  n_width = 256
  n_height = 512
  n_cell_width = 14
  n_cell_height = 16
  n_baseline = 11

  def __init__(self, char_table: dict[str, str] = {}):
    super().__init__(char_table)
    char_table["・"] = "·"
    self.font = GdiFont("C:/Windows/Fonts/simsun.ttc", "宋体", 12)

  def needs_redraw(self, char: str) -> bool:
    if 0x4E00 <= ord(char) <= 0x9FFF:
      return True

    return False

  def draw(self, char: str) -> tuple[Image.Image, CWDHInfo]:
    glyph = self.draw_glyph(char)
    image = Image.new("RGBA", (self.n_cell_width, self.n_cell_height))
    image.paste(glyph.image, (1 + glyph.left, 1 + self.n_baseline - glyph.ascent))
    return image, CWDHInfo(0, 13, 13)

  def draw_glyph(self, char: str) -> Glyph:
    glyph = self.font.draw(self.char_table.get(char, char), 1)
    size = (glyph.image.width + 2, glyph.image.height + 2)
    foreground = Image.new("L", size)
    foreground.paste(glyph.image.getchannel("A"), (1, 1))
    alpha = Image.new("L", size)
    for y in (-1, 0, 1):
      for x in (-1, 0, 1):
        layer = Image.new("L", size)
        layer.paste(glyph.image.getchannel("A"), (1 + x, 1 + y))
        alpha = ImageChops.lighter(alpha, layer)
    image = Image.new("RGBA", size)
    image.putalpha(alpha)
    image.paste((255, 255, 255, 255), (0, 0, *size), foreground)
    return Glyph(image, glyph.left, glyph.ascent + 1, 13)

  def close(self):
    self.font.close()


def create_new_font(
  file_name: str,
  input_dir: str,
  output_dir: str,
  config: IDrawConfg,
  high_res_dir: str,
):
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  font = BCFNT.from_file(f"{input_dir}/{file_name}")

  format = font.tglp.image_format

  o_width = font.tglp.image_width
  o_height = font.tglp.image_height
  o_cell_width = font.tglp.cell_width + 1
  o_cell_height = font.tglp.cell_height + 1

  o_images = [sheet_to_image(i, o_width, o_height, format) for i in font.tglp.image_data]

  o_max_x = font.tglp.cells_per_row
  o_max_y = font.tglp.cells_per_column
  o_max_xy = o_max_x * o_max_y

  o_index_map = {v: k for k, v in font.char_map.items()}

  n_char_codes: list[int] = []
  n_glyphs: list[Glyph] = []
  n_high_res_glyphs: list[Glyph] = []
  n_width_info: list[CWDHInfo] = []

  for char in config.get_new_chars(font.char_map):
    if config.needs_redraw(char):
      glyph = config.draw_glyph(char)
    else:
      code = o_index_map.get(ord(char), None)
      if code is None:
        continue

      o_sheet_i = code // o_max_xy
      o_cell_i = code % o_max_xy
      o_y = o_cell_i // o_max_x
      o_x = o_cell_i % o_max_x
      o_width_info = font.width_map[code]

      glyph = o_images[o_sheet_i].crop(
        (
          o_x * o_cell_width + 1,
          o_y * o_cell_height + 1,
          o_x * o_cell_width + 1 + o_width_info.width,
          o_y * o_cell_height + 1 + font.tglp.cell_height,
        )
      )
      bbox = glyph.getbbox()
      if bbox:
        glyph = Glyph(glyph.crop(bbox), o_width_info.start + bbox[0], font.tglp.baseline - bbox[1], o_width_info.length)
      else:
        glyph = Glyph(Image.new("RGBA", (0, 0)), o_width_info.start, 0, o_width_info.length)

    if glyph.image.height > config.n_cell_height - 1:
      height = config.n_cell_height - 1
      glyph.ascent = round(glyph.ascent * height / glyph.image.height)
      glyph.image = glyph.image.resize((glyph.image.width, height), Image.Resampling.LANCZOS)
    y = min(max(config.n_baseline - glyph.ascent, 0), config.n_cell_height - 1 - glyph.image.height)
    glyph.ascent = config.n_baseline - y

    high_res_glyph = config.draw_high_res(char, glyph)
    if glyph.image.width and high_res_glyph.image.width:
      scale = min(glyph.image.width * 8 / high_res_glyph.image.width, glyph.image.height * 8 / high_res_glyph.image.height)
      size = (max(1, round(high_res_glyph.image.width * scale)), max(1, round(high_res_glyph.image.height * scale)))
      high_res_glyph.image = high_res_glyph.image.resize(size, Image.Resampling.LANCZOS)
      high_res_glyph.left = glyph.left * 8 + (glyph.image.width * 8 - size[0]) // 2
      high_res_glyph.ascent = glyph.ascent * 8 - (glyph.image.height * 8 - size[1]) // 2
    width = CWDHInfo(glyph.left, glyph.image.width, glyph.advance)
    n_glyphs.append(glyph)
    n_high_res_glyphs.append(high_res_glyph)
    n_width_info.append(width)

    n_char_codes.append(ord(char))

  n_width = config.n_width
  n_height = config.n_height
  n_baseline = config.n_baseline
  n_cell_width = config.n_cell_width
  n_cell_height = config.n_cell_height

  n_max_x = n_width // n_cell_width
  n_max_y = n_height // n_cell_height
  n_max_xy = n_max_x * n_max_y

  n_char_map = dict(enumerate(n_char_codes))
  default_char = font.char_map[font.finf.default_glyph_index]
  font.finf.default_glyph_index = n_char_codes.index(default_char)
  font.cmaps = BCFNT.compress_cmap(n_char_map)

  font.char_map = n_char_map
  font.cwdhs[0].info = n_width_info
  font.cwdhs[0].last_index = len(n_glyphs) - 1

  n_images: list[Image.Image] = [
    Image.new("RGBA", (n_width, n_height)) for _ in range((len(n_glyphs) + n_max_xy - 1) // n_max_xy)
  ]

  for code, char in n_char_map.items():
    n_sheet_i = code // n_max_xy
    n_cell_i = code % n_max_xy
    n_y = n_cell_i // n_max_x
    n_x = n_cell_i % n_max_x

    glyph = n_glyphs[code]
    n_images[n_sheet_i].paste(
      glyph.image,
      (n_x * n_cell_width + 1 + glyph.left - n_width_info[code].start, n_y * n_cell_height + 1 + n_baseline - glyph.ascent),
    )

  os.makedirs(high_res_dir, exist_ok=True)
  for sheet_i in range(len(n_images)):
    image = Image.new("RGBA", (n_width * 8, n_height * 8))
    for code in range(sheet_i * n_max_xy, min((sheet_i + 1) * n_max_xy, len(n_glyphs))):
      cell_i = code % n_max_xy
      y = cell_i // n_max_x
      x = cell_i % n_max_x
      glyph = n_high_res_glyphs[code]
      image.paste(
        glyph.image,
        ((x * n_cell_width + 1 - n_width_info[code].start) * 8 + glyph.left, (y * n_cell_height + 1 + n_baseline) * 8 - glyph.ascent),
      )
    image.save(f"{high_res_dir}/{sheet_i:04d}.png")

  font.tglp.image_data = [image_to_sheet(image, format) for image in n_images]
  font.tglp.image_count = len(n_images)
  font.tglp.image_width = n_width
  font.tglp.image_height = n_height
  font.tglp.image_size = len(font.tglp.image_data[0])
  font.tglp.cell_width = n_cell_width - 1
  font.tglp.cell_height = n_cell_height - 1
  font.tglp.cells_per_row = n_max_x
  font.tglp.cells_per_column = n_max_y
  font.tglp.baseline = n_baseline
  font.tglp.max_char_width = max(width.length for width in n_width_info)

  BCFNT.to_file(font, f"{output_dir}/{file_name}")


if __name__ == "__main__":
  create_list = [
    (PATH_CHAR_TABLE_XY, PATH_GARC_FONT_XY),
    (PATH_CHAR_TABLE_ORAS, PATH_GARC_FONT_ORAS),
    (PATH_CHAR_TABLE_ORAS_DEMO, PATH_GARC_FONT_ORAS_DEMO),
  ]

  for char_table_path, garc_font_path in create_list:
    with open(char_table_path, "r", -1, "utf8") as reader:
      char_table = {char: char for char in reader.read()}

    config = DrawConfig1(char_table)
    create_new_font(
      "0001.bin",
      f"unpacked/japanese/{garc_font_path}",
      f"temp/import/japanese/{garc_font_path}",
      config,
      f"temp/high_res/japanese/{garc_font_path}/0001",
    )
    config.close()
    shutil.copy(f"temp/import/japanese/{garc_font_path}/0001.bin", f"temp/import/japanese/{garc_font_path}/0000.bin")
    config = DrawConfig2(char_table)
    create_new_font(
      "0002.bin",
      f"unpacked/japanese/{garc_font_path}",
      f"temp/import/japanese/{garc_font_path}",
      config,
      f"temp/high_res/japanese/{garc_font_path}/0002",
    )
    config.close()
