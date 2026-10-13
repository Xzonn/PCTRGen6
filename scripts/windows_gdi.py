import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from PIL import Image


class LOGFONTW(ctypes.Structure):
  _fields_ = [
    ("lfHeight", wintypes.LONG),
    ("lfWidth", wintypes.LONG),
    ("lfEscapement", wintypes.LONG),
    ("lfOrientation", wintypes.LONG),
    ("lfWeight", wintypes.LONG),
    ("lfItalic", wintypes.BYTE),
    ("lfUnderline", wintypes.BYTE),
    ("lfStrikeOut", wintypes.BYTE),
    ("lfCharSet", wintypes.BYTE),
    ("lfOutPrecision", wintypes.BYTE),
    ("lfClipPrecision", wintypes.BYTE),
    ("lfQuality", wintypes.BYTE),
    ("lfPitchAndFamily", wintypes.BYTE),
    ("lfFaceName", wintypes.WCHAR * 32),
  ]


class FIXED(ctypes.Structure):
  _fields_ = [("fract", wintypes.WORD), ("value", ctypes.c_short)]


class MAT2(ctypes.Structure):
  _fields_ = [("eM11", FIXED), ("eM12", FIXED), ("eM21", FIXED), ("eM22", FIXED)]


class GLYPHMETRICS(ctypes.Structure):
  _fields_ = [
    ("gmBlackBoxX", wintypes.UINT),
    ("gmBlackBoxY", wintypes.UINT),
    ("gmptGlyphOrigin", wintypes.POINT),
    ("gmCellIncX", ctypes.c_short),
    ("gmCellIncY", ctypes.c_short),
  ]


gdi = ctypes.WinDLL("gdi32", use_last_error=True)
gdi.AddFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
gdi.AddFontResourceExW.restype = ctypes.c_int
gdi.RemoveFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
gdi.RemoveFontResourceExW.restype = wintypes.BOOL
gdi.CreateDCW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID]
gdi.CreateDCW.restype = wintypes.HDC
gdi.CreateFontIndirectW.argtypes = [ctypes.POINTER(LOGFONTW)]
gdi.CreateFontIndirectW.restype = wintypes.HFONT
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi.SelectObject.restype = wintypes.HGDIOBJ
gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi.DeleteObject.restype = wintypes.BOOL
gdi.DeleteDC.argtypes = [wintypes.HDC]
gdi.DeleteDC.restype = wintypes.BOOL
gdi.GetGlyphIndicesW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.WORD), wintypes.DWORD]
gdi.GetGlyphIndicesW.restype = wintypes.DWORD
gdi.GetGlyphOutlineW.argtypes = [
  wintypes.HDC, wintypes.UINT, wintypes.UINT, ctypes.POINTER(GLYPHMETRICS),
  wintypes.DWORD, wintypes.LPVOID, ctypes.POINTER(MAT2),
]
gdi.GetGlyphOutlineW.restype = wintypes.DWORD


def check(value):
  if not value:
    raise ctypes.WinError(ctypes.get_last_error())
  return value


@dataclass
class Glyph:
  image: Image.Image
  left: int
  ascent: int
  advance: int

  def resize(self, scale):
    return Glyph(
      self.image.resize((self.image.width * scale, self.image.height * scale), Image.Resampling.NEAREST)
      if self.image.width and self.image.height else Image.new("RGBA", (0, 0)),
      self.left * scale,
      self.ascent * scale,
      self.advance * scale,
    )


class GdiFont:
  def __init__(self, path, name, size):
    self.path = path
    check(gdi.AddFontResourceExW(path, 0x10, None))
    self.dc = check(gdi.CreateDCW("DISPLAY", None, None, None))
    logfont = LOGFONTW()
    logfont.lfHeight = -size
    logfont.lfWeight = 400
    logfont.lfCharSet = 1
    logfont.lfQuality = 4
    logfont.lfFaceName = name
    self.font = check(gdi.CreateFontIndirectW(ctypes.byref(logfont)))
    self.old_font = check(gdi.SelectObject(self.dc, self.font))

  def draw(self, char, bpp=8):
    glyph_index = wintypes.WORD()
    result = gdi.GetGlyphIndicesW(self.dc, char, 1, ctypes.byref(glyph_index), 1)
    assert result != 0xFFFFFFFF and glyph_index.value != 0xFFFF, char
    metrics = GLYPHMETRICS()
    matrix = MAT2(FIXED(0, 1), FIXED(0, 0), FIXED(0, 0), FIXED(0, 1))
    mode = {1: 1, 4: 5, 8: 6}[bpp]
    size = gdi.GetGlyphOutlineW(self.dc, ord(char), mode, ctypes.byref(metrics), 0, None, ctypes.byref(matrix))
    assert size != 0xFFFFFFFF, char
    width = metrics.gmBlackBoxX
    height = metrics.gmBlackBoxY
    left = metrics.gmptGlyphOrigin.x
    ascent = metrics.gmptGlyphOrigin.y
    advance = metrics.gmCellIncX
    if size:
      buffer = ctypes.create_string_buffer(size)
      result = gdi.GetGlyphOutlineW(self.dc, ord(char), mode, ctypes.byref(metrics), size, buffer, ctypes.byref(matrix))
      assert result != 0xFFFFFFFF, char
      stride = ((width + 31) // 32) * 4 if bpp == 1 else ((width + 3) // 4) * 4
      image = Image.frombytes("1" if bpp == 1 else "L", (stride * 8 if bpp == 1 else stride, height), buffer.raw)
      image = image.convert("L").crop((0, 0, width, height))
    else:
      image = Image.new("L", (0, 0))
    if bpp > 1:
      levels = (1 << bpp) - 1
      denominator = 16 if bpp == 4 else 64
      image = image.point([min(value * levels // denominator, levels) * 255 // levels for value in range(256)])
    bbox = image.getbbox()
    if bbox:
      image = image.crop(bbox)
      left += bbox[0]
      ascent -= bbox[1]
    else:
      image = Image.new("L", (0, 0))
      left = advance
      ascent = 0
    result = Image.new("RGBA", image.size)
    result.putalpha(image)
    return Glyph(result, left, ascent, advance)

  def close(self):
    check(gdi.SelectObject(self.dc, self.old_font))
    check(gdi.DeleteObject(self.font))
    check(gdi.DeleteDC(self.dc))
    check(gdi.RemoveFontResourceExW(self.path, 0x10, None))
