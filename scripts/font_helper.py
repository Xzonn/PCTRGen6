import struct
from typing import Generator

from PIL import Image

FORMAT_RGBA8 = 0x00
FORMAT_RGB8 = 0x01
FORMAT_RGBA5551 = 0x02
FORMAT_RGB565 = 0x03
FORMAT_RGBA4 = 0x04
FORMAT_LA8 = 0x05
FORMAT_HILO8 = 0x06
FORMAT_L8 = 0x07
FORMAT_A8 = 0x08
FORMAT_LA4 = 0x09
FORMAT_L4 = 0x0A
FORMAT_A4 = 0x0B
FORMAT_ETC1 = 0x0C
FORMAT_ETC1A4 = 0x0D

PIXEL_FORMATS = {
  FORMAT_RGBA8: "RGBA8",
  FORMAT_RGB8: "RGB8",
  FORMAT_RGBA5551: "RGBA5551",
  FORMAT_RGB565: "RGB565",
  FORMAT_RGBA4: "RGBA4",
  FORMAT_LA8: "LA8",
  FORMAT_HILO8: "HILO8",
  FORMAT_L8: "L8",
  FORMAT_A8: "A8",
  FORMAT_LA4: "LA4",
  FORMAT_L4: "L4",
  FORMAT_A4: "A4",
  FORMAT_ETC1: "ETC1",
  FORMAT_ETC1A4: "ETC1A4",
}

PIXEL_FORMAT_SIZE = {
  FORMAT_RGBA8: 32,
  FORMAT_RGB8: 24,
  FORMAT_RGBA5551: 16,
  FORMAT_RGB565: 16,
  FORMAT_RGBA4: 16,
  FORMAT_LA8: 16,
  FORMAT_HILO8: 16,
  FORMAT_L8: 8,
  FORMAT_A8: 8,
  FORMAT_LA4: 8,
  FORMAT_L4: 4,
  FORMAT_A4: 4,
  FORMAT_ETC1: 64,
  FORMAT_ETC1A4: 128,
}


def get_pixel_pos(width: int, height: int) -> Generator[tuple[int, int, int], tuple[int, int], None]:
  for tile_y in range(height // 8):
    for tile_x in range(width // 8):
      # tile is composed of 2x2 sub-tiles
      for y in range(2):
        for x in range(2):
          # sub-tile is composed of 2x2 pixel groups
          for y2 in range(2):
            for x2 in range(2):
              # pixel group is composed of 2x2 pixels (finally)
              for y3 in range(2):
                for x3 in range(2):
                  # if the final y value is beyond the input data's height then don't read it
                  if tile_y + y + y2 + y3 >= height:
                    continue
                  # same for the x and the input data width
                  if tile_x + x + x2 + x3 >= width:
                    continue

                  pixel_x = x3 + (x2 * 2) + (x * 4) + (tile_x * 8)
                  pixel_y = y3 + (y2 * 2) + (y * 4) + (tile_y * 8)

                  data_x = x3 + (x2 * 4) + (x * 16) + (tile_x * 64)
                  data_y = (y3 * 2) + (y2 * 8) + (y * 32) + (tile_y * width * 8)

                  yield pixel_x, pixel_y, data_x + data_y


def data_to_rgba(data: bytes, format: int, index: int) -> tuple[int, int, int, int]:
  red = green = blue = alpha = 0

  # rrrrrrrr gggggggg bbbbbbbb aaaaaaaa
  if format == FORMAT_RGBA8:
    red, green, blue, alpha = struct.unpack("4B", data[index * 4 : index * 4 + 4])

  # rrrrrrrr gggggggg bbbbbbbb
  elif format == FORMAT_RGB8:
    red, green, blue = struct.unpack("3B", data[index * 3 : index * 3 + 3])
    alpha = 255

  # rrrrrgg gggbbbbba
  elif format == FORMAT_RGBA5551:
    b1, b2 = struct.unpack("2B", data[index * 2 : index * 2 + 2])

    red = (b1 >> 3) & 0x1F
    green = (b1 & 0x07) | ((b2 >> 6) & 0x03)
    blue = (b2 >> 1) & 0x1F
    alpha = (b2 & 0x01) * 255

  # rrrrrggg gggbbbbb
  elif format == FORMAT_RGB565:
    b1, b2 = struct.unpack("2B", data[index * 2 : index * 2 + 2])

    red = (b1 >> 3) & 0x1F
    green = (b1 & 0x7) | ((b2 >> 5) & 0x7)
    blue = b2 & 0x1F
    alpha = 255

  # rrrrgggg bbbbaaaa
  elif format == FORMAT_RGBA4:
    b1, b2 = struct.unpack("2B", data[index * 2 : index * 2 + 2])

    red = ((b1 >> 4) & 0x0F) * 0x11
    alpha = (b1 & 0x0F) * 0x11
    blue = ((b2 >> 4) & 0x0F) * 0x11
    green = (b2 & 0x0F) * 0x11

  # llllllll aaaaaaaa
  elif format == FORMAT_LA8:
    l, alpha = struct.unpack("2B", data[index * 2 : index * 2 + 2])
    red = green = blue = l

  # ??
  elif format == FORMAT_HILO8:
    # TODO
    pass

  # llllllll
  elif format == FORMAT_L8:
    red = green = blue = struct.unpack("B", data[index : index + 1])[0]
    alpha = 255

  # aaaaaaaa
  elif format == FORMAT_A8:
    alpha = struct.unpack("B", data[index : index + 1])[0]
    red = green = blue = 0

  # llllaaaa
  elif format == FORMAT_LA4:
    la = struct.unpack("B", data[index : index + 1])[0]
    red = green = blue = ((la >> 4) & 0x0F) * 0x11
    alpha = (la & 0x0F) * 0x11

  # llll
  elif format == FORMAT_L4:
    l = data[index // 2]
    shift = (index & 1) * 4
    red = green = blue = ((l >> shift) & 0x0F) * 0x11
    alpha = 255

  # aaaa
  elif format == FORMAT_A4:
    byte = data[index // 2]
    shift = (index & 1) * 4
    alpha = ((byte >> shift) & 0x0F) * 0x11
    green = red = blue = 0

  return red, green, blue, alpha


def rgba_to_data(red: int, green: int, blue: int, alpha: int, format: int) -> bytes:
  output: list[int] = []
  if format == FORMAT_RGBA8:
    output = [red, green, blue, alpha]

  elif format == FORMAT_RGB8:
    output = [red, green, blue]

  # rrrrrggg ggbbbbba
  elif format == FORMAT_RGBA5551:
    r5 = (red // 8) & 0x1F
    g5 = (green // 8) & 0x1F
    b5 = (blue // 8) & 0x1F
    a = 1 if alpha > 0 else 0

    b1 = (r5 << 3) | (g5 >> 2)
    b2 = ((g5 << 6) | (b5 << 1) | a) & 0xFF
    output = [b1, b2]

  # rrrrrggg gggbbbbb
  elif format == FORMAT_RGB565:
    r5 = (red // 8) & 0x1F
    g6 = (green // 4) & 0x3F
    b5 = (blue // 8) & 0x1F

    b1 = (r5 << 3) | (g6 >> 3)
    b2 = ((g6 << 5) | b5) & 0xFF
    output = [b1, b2]

  # rrrrgggg bbbbaaaa
  elif format == FORMAT_RGBA4:
    r4 = (red // 0x11) & 0x0F
    g4 = (green // 0x11) & 0x0F
    b4 = (blue // 0x11) & 0x0F
    a4 = (alpha // 0x11) & 0x0F

    b1 = (r4 << 4) | g4
    b2 = (b4 << 4) | a4
    output = [b1, b2]

  # llllllll aaaaaaaa
  elif format == FORMAT_LA8:
    l = int((red * 0.2126) + (green * 0.7152) + (blue * 0.0722))

    output = [l, alpha]

  elif format == FORMAT_HILO8:
    # TODO
    pass

  # llllllll
  elif format == FORMAT_L8:
    l = int((red * 0.2126) + (green * 0.7152) + (blue * 0.0722))

    output = [l]

  # aaaaaaaa
  elif format == FORMAT_A8:
    output = [alpha]

  # llllaaaa
  elif format == FORMAT_LA4:
    l = round((red * 0.2126) + (green * 0.7152) + (blue * 0.0722)) // 0x11
    a = (alpha // 0x11) & 0x0F

    b = (l << 4) | a
    output = [b]

  # llll
  elif format == FORMAT_L4:
    l = int((red * 0.2126) + (green * 0.7152) + (blue * 0.0722))
    output = [l]

  # aaaa
  elif format == FORMAT_A4:
    a = (alpha // 0x11) & 0xF
    output = [a]

  return bytes(output)


def sheet_to_image(data: bytes, width: int, height: int, format: int) -> Image.Image:
  image = Image.new("RGBA", (width, height))

  for pixel_x, pixel_y, data_pos in get_pixel_pos(width, height):
    r, g, b, a = data_to_rgba(data, format, data_pos)
    image.putpixel((pixel_x, pixel_y), (r, g, b, a))

  return image


def image_to_sheet(image: Image.Image, format: int) -> bytes:
  width, height = image.size
  data = bytearray(width * height * PIXEL_FORMAT_SIZE[format] // 8)

  for pixel_x, pixel_y, data_pos in get_pixel_pos(width, height):
    r, g, b, a = image.getpixel((pixel_x, pixel_y)) # type: ignore
    pixel_data = rgba_to_data(r, g, b, a, format)
    if PIXEL_FORMAT_SIZE[format] == 4:
      shift = (data_pos & 1) * 4
      data[data_pos // 2] |= pixel_data[0] << shift
    else:
      data[data_pos:data_pos + len(pixel_data)] = pixel_data

  return bytes(data)
