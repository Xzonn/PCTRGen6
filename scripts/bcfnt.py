import struct
from typing import Literal, TypeAlias

Endianess: TypeAlias = Literal["<", ">"]


class FINF:
  def __init__(self, data: bytes, offset: int = 0, endianess: Endianess = "<"):
    magic, block_size = struct.unpack_from(f"{endianess}4sI", data, offset)
    self.block_size: int = block_size

    assert magic == b"FINF"
    assert block_size == 0x20

    font_type, line_height, default_glyph_index, default_start, default_width, default_length, encoding = (
      struct.unpack_from(f"{endianess}2BH4B", data, offset + 0x08)
    )
    self.font_type: int = font_type
    self.line_height: int = line_height
    self.default_glyph_index: int = default_glyph_index
    self.default_start: int = default_start
    self.default_width: int = default_width
    self.default_length: int = default_length
    self.encoding: int = encoding

    tglp_offset, cwdh_offset, cmap_offset = struct.unpack_from(f"{endianess}3I", data, offset + 0x10)
    self.tglp_offset: int = tglp_offset
    self.cwdh_offset: int = cwdh_offset
    self.cmap_offset: int = cmap_offset

    font_height, font_width, bearing_y, bearing_x = struct.unpack_from(f"{endianess}4B", data, offset + 0x1C)
    self.font_height: int = font_height
    self.font_width: int = font_width
    self.bearing_y: int = bearing_y
    self.bearing_x: int = bearing_x

  def get_bytes(self, endianess: Endianess = "<") -> bytes:
    head = struct.pack(
      f"{endianess}4sI2BH4B3I4B",
      b"FINF",
      0x20,
      self.font_type,
      self.line_height,
      self.default_glyph_index,
      self.default_start,
      self.default_width,
      self.default_length,
      self.encoding,
      self.tglp_offset,
      self.cwdh_offset,
      self.cmap_offset,
      self.font_height,
      self.font_width,
      self.bearing_y,
      self.bearing_x,
    )
    return bytes(head)


class TGLP:
  def __init__(self, data: bytes, offset: int = 0, endianess: Endianess = "<"):
    magic, block_size = struct.unpack_from(f"{endianess}4sI", data, offset)

    assert magic == b"TGLP"

    cell_width, cell_height, baseline, max_char_width, image_size = struct.unpack_from(
      f"{endianess}4BI", data, offset + 0x08
    )
    image_count, image_format, cells_per_row, cells_per_column, image_width, image_height, image_offset = (
      struct.unpack_from(f"{endianess}6HI", data, offset + 0x10)
    )

    # assert image_offset == 0x80

    self.cell_width: int = cell_width
    self.cell_height: int = cell_height
    self.baseline: int = baseline
    self.max_char_width: int = max_char_width
    self.image_size: int = image_size
    self.image_count: int = image_count
    self.image_format: int = image_format
    self.cells_per_row: int = cells_per_row
    self.cells_per_column: int = cells_per_column
    self.image_width: int = image_width
    self.image_height: int = image_height
    self.image_offset: int = image_offset
    self.image_data: list[bytes] = []

    for i in range(self.image_count):
      self.image_data.append(data[image_offset + i * self.image_size : image_offset + (i + 1) * self.image_size])

  def get_bytes(self, endianess: Endianess = "<") -> bytes:
    body = bytearray()
    for i in range(self.image_count):
      body.extend(self.image_data[i])

    assert self.image_offset == 0x80

    head = (
      struct.pack(
        f"{endianess}4sI4BI6HI",
        b"TGLP",
        0x4C + len(body),
        self.cell_width,
        self.cell_height,
        self.baseline,
        self.max_char_width,
        self.image_size,
        self.image_count,
        self.image_format,
        self.cells_per_row,
        self.cells_per_column,
        self.image_width,
        self.image_height,
        self.image_offset,
      )
      + b"\0" * 0x2C
    )
    return bytes(head + body)


class CWDHInfo:
  def __init__(self, start: int, width: int, length: int):
    self.start: int = start
    self.width: int = width
    self.length: int = length

  def get_bytes(self) -> bytes:
    return struct.pack("<b2B", self.start, self.width, self.length)


class CWDH:
  def __init__(self, data: bytes, offset: int = 0, endianess: Endianess = "<"):
    magic, block_size = struct.unpack_from(f"{endianess}4sI", data, offset)

    assert magic == b"CWDH"

    first_code, last_code, next_offset = struct.unpack_from(f"{endianess}2HI", data, offset + 0x08)
    self.first_code: int = first_code
    self.last_index: int = last_code
    self.cwdh_offset: int = next_offset

    self.info: list[CWDHInfo] = []
    for i in range(0, (block_size - 0x10) // 3):
      start, width, length = struct.unpack_from("<b2B", data, offset + 0x10 + 3 * i)
      self.info.append(CWDHInfo(start, width, length))

  def get_bytes(self, endianess: Endianess = "<") -> bytes:
    body = bytearray()
    for info in self.info:
      body += info.get_bytes()
    body += b"\0" * (-len(body) % 4)

    head = struct.pack(
      f"{endianess}4sI2HI",
      b"CWDH",
      0x10 + len(body),
      self.first_code,
      self.last_index,
      0,
    )
    return bytes(head + body)


class CMAP:
  def __init__(self, data: bytes, offset: int = 0, endianess: Endianess = "<"):
    magic, block_size = struct.unpack_from(f"{endianess}4sI", data, offset)

    assert magic == b"CMAP"

    first_char_code, last_char_code, type_section, unk_1, cmap_offset = struct.unpack_from(
      f"{endianess}4HI",
      data,
      offset + 0x08,
    )

    assert unk_1 == 0

    self.first_char_code: int = first_char_code
    self.last_char_code: int = last_char_code
    self.type_section: int = type_section
    self.cmap_offset: int = cmap_offset

    self.index_map: dict[int, int] = {}
    if self.type_section == 0:
      (first_char_index,) = struct.unpack_from(f"{endianess}H", data, offset + 0x14)
      for i in range(last_char_code - first_char_code + 1):
        char_index = first_char_index + i
        self.index_map[first_char_code + i] = char_index
    elif self.type_section == 1:
      length = last_char_code - first_char_code + 1
      for i in range(length):
        (char_index,) = struct.unpack_from(f"{endianess}H", data, offset + 0x14 + 2 * i)
        if char_index == 0xFFFF:
          continue
        self.index_map[first_char_code + i] = char_index
    elif self.type_section == 2:
      (num_chars,) = struct.unpack_from(f"{endianess}H", data, offset + 0x14)
      for i in range(num_chars):
        char_code, char_index = struct.unpack_from(f"{endianess}2H", data, offset + 0x16 + 4 * i)
        self.index_map[char_code] = char_index

  @property
  def char_map(self) -> dict[int, int]:
    return {v: k for k, v in self.index_map.items()}

  @staticmethod
  def get_blank():
    return CMAP(b"CMAP" + b"\0" * 0x12)

  def get_bytes(self, index_map: dict[int, int] | None = None, endianess: Endianess = "<"):
    if index_map is None:
      index_map = self.index_map
    sorted_keys = sorted(index_map.keys(), key=lambda x: index_map[x])
    body = bytearray()
    if self.type_section == 0:
      for char_code, char_index in index_map.items():
        body += struct.pack(f"{endianess}H", char_index)
        break
    elif self.type_section == 1:
      length = self.last_char_code - self.first_char_code + 1
      for i in range(length):
        char_code = self.first_char_code + i
        char_index = index_map.get(char_code, 0xFFFF)
        body += struct.pack(f"{endianess}H", char_index)
    elif self.type_section == 2:
      body += struct.pack(f"{endianess}H", len(index_map))
      for key in sorted_keys:
        body += struct.pack(f"{endianess}2H", key, index_map[key])

    body += b"\0" * (-len(body) % 4)

    head = struct.pack(
      f"{endianess}4sI4HI",
      b"CMAP",
      0x14 + len(body),
      self.first_char_code,
      self.last_char_code,
      self.type_section,
      0,
      0,
    )
    return bytes(head + body)


class BCFNT:
  endianess: Endianess

  def __init__(self, data: bytes):
    self.data = data

    magic = data[:4]
    assert magic == b"CFNT"

    (bom,) = struct.unpack_from("<H", data, 4)
    if bom == 0xFEFF:
      endianess = self.endianess = "<"
    elif bom == 0xFFFE:
      endianess = self.endianess = ">"
    else:
      raise ValueError(f"Unknown BOM: {bom:04X}")

    block_size, version, file_size, num_blocks = struct.unpack_from(f"{endianess}H3I", data, 6)

    assert block_size == 0x14

    self.version: int = version
    self.num_blocks: int = num_blocks

    self.finf: FINF = FINF(data, block_size, endianess)
    self.tglp: TGLP = TGLP(data, self.finf.tglp_offset - 8, endianess)

    self.width_map: dict[int, CWDHInfo] = {}
    self.cwdhs: list[CWDH] = []
    next_offset = self.finf.cwdh_offset - 8
    while next_offset < len(data):
      cwdh: CWDH = CWDH(data, next_offset, endianess)
      for i, info in enumerate(cwdh.info):
        self.width_map[cwdh.first_code + i] = info
      self.cwdhs.append(cwdh)
      if cwdh.cwdh_offset == 0:
        break
      next_offset = cwdh.cwdh_offset - 8

    self.char_map: dict[int, int] = {}
    self.cmaps: list[CMAP] = []
    next_offset = self.finf.cmap_offset - 8
    while next_offset < len(data):
      cmap: CMAP = CMAP(data, next_offset, endianess)
      self.cmaps.append(cmap)
      self.char_map.update(cmap.char_map)
      if cmap.cmap_offset == 0:
        break
      next_offset = cmap.cmap_offset - 8

  def get_bytes(self, endianess: Endianess = "<") -> bytes:
    cmaps = [cmap.get_bytes(endianess=endianess) for cmap in self.cmaps]
    cwdhs = [cwdh.get_bytes(endianess=endianess) for cwdh in self.cwdhs]
    tglp = self.tglp.get_bytes(endianess=endianess)

    self.finf.tglp_offset = 0x1C + self.finf.block_size
    self.finf.cwdh_offset = self.finf.tglp_offset + len(tglp)
    next_offset = self.finf.cmap_offset
    for i, cwdh in enumerate(cwdhs[:-1]):
      next_offset += len(cwdh)
      cwdhs[i] = cwdh[:0x0C] + struct.pack(f"{endianess}I", next_offset) + cwdh[0x10:]

    self.finf.cmap_offset = self.finf.cwdh_offset + sum(len(cwdh) for cwdh in cwdhs)
    next_offset = self.finf.cmap_offset
    for i, cmap in enumerate(cmaps[:-1]):
      next_offset += len(cmap)
      cmaps[i] = cmap[:0x10] + struct.pack(f"{endianess}I", next_offset) + cmap[0x14:]

    finf = self.finf.get_bytes(endianess=endianess)

    body = finf + tglp + b"".join(cwdhs) + b"".join(cmaps)

    head = struct.pack(
      f"{endianess}4s2H3I",
      b"CFNT",
      0xFEFF,
      0x14,
      self.version,
      0x14 + len(body),
      0x02 + len(cwdhs) + len(cmaps),
    )
    return bytes(head + body)

  @staticmethod
  def compress_cmap(char_map: dict[int, int]) -> list[CMAP]:
    cmaps = []
    type_2_index_map = {}

    char_index = 0
    char_map_len = len(char_map)
    while char_index < len(char_map):
      char_code = char_map[char_index]

      code_index_diff = char_code - char_index
      window = 0x20
      while (
        char_index + window < char_map_len and char_map[char_index + window] - (char_index + window) == code_index_diff
      ):
        window += 1
      if window > 0x20:
        cmap = CMAP.get_blank()
        cmap.type_section = 0
        cmap.first_char_code = char_code
        cmap.last_char_code = char_map[char_index + window - 1]
        cmap.index_map = {char_map[index]: index for index in range(char_index, char_index + window)}
        cmaps.append(cmap)
        char_index += window
        continue

      window = 0
      while char_index + window < char_map_len and char_map[char_index + window] - char_code <= window * 2:
        if char_index + window > 0 and char_map[char_index + window] - char_map[char_index + window - 1] > 0x10:
          break
        window += 1

      if window > 0x20:
        cmap = CMAP.get_blank()
        cmap.type_section = 1
        cmap.first_char_code = char_code
        cmap.last_char_code = char_map[char_index + window - 1]
        cmap.index_map = {char_map[index]: index for index in range(char_index, char_index + window)}
        cmaps.append(cmap)

        char_index += window
        continue

      type_2_index_map[char_code] = char_index
      char_index += 1
      continue

    if type_2_index_map:
      cmap = CMAP.get_blank()
      cmap.type_section = 2
      cmap.first_char_code = min(type_2_index_map.values())
      cmap.last_char_code = 0xFFFF
      cmap.index_map = type_2_index_map
      cmaps.append(cmap)

    return cmaps

  @staticmethod
  def from_file(path: str) -> "BCFNT":
    with open(path, "rb") as reader:
      data = reader.read()
    return BCFNT(data)

  @staticmethod
  def to_file(bcfnt: "BCFNT", path: str):
    with open(path, "wb") as writer:
      writer.write(bcfnt.get_bytes())
