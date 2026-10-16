$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

if (-not (Test-Path "unpacked\japanese\XY\a\0\7\2")) {
  & $tool "export" -p "original_files\japanese\XY" -o "unpacked\japanese\XY"
}

python scripts/create_new_font.py XY
python scripts/compile_exefs_patch.py XY

& $tool "import-text" -p "unpacked\japanese\XY\a\0\7\2" -r "texts\XY\zh_Hans\gametext" -o "temp\import\japanese\XY\a\0\7\2"
& $tool "import-text" -p "unpacked\japanese\XY\a\0\7\3" -r "texts\XY\zh_Hans\gametext" -o "temp\import\japanese\XY\a\0\7\3" -e "texts\XY\zh_Latn\gametext"
& $tool "import-text" -p "unpacked\japanese\XY\a\0\7\4" -r "texts\XY\zh_Hans\gametext" -o "temp\import\japanese\XY\a\0\7\4" -e "texts\XY\zh_Hant\gametext"
& $tool "import-text" -p "unpacked\japanese\XY\a\0\7\9" -r "texts\XY\zh_Hans\gametext" -o "temp\import\japanese\XY\a\0\7\4" -e "texts\XY\ko\gametext"

& $tool "import-text" -p "unpacked\japanese\XY\a\0\8\0" -r "texts\XY\zh_Hans\storytext" -o "temp\import\japanese\XY\a\0\8\0"
& $tool "import-text" -p "unpacked\japanese\XY\a\0\8\1" -r "texts\XY\zh_Hans\storytext" -o "temp\import\japanese\XY\a\0\8\1"
& $tool "import-text" -p "unpacked\japanese\XY\a\0\8\2" -r "texts\XY\zh_Hans\storytext" -o "temp\import\japanese\XY\a\0\8\2"

& $tool "import" -p "original_files\japanese\XY" -r "temp\import\japanese\XY" -o "temp\output\japanese\XY"

python scripts/build_patches.py XY

if (Test-Path "$env:APPDATA\Citra\load\mods\0004000000055D00\romfs\") {
  Copy-Item -Path "temp\output\japanese\XY\*" -Destination "$env:APPDATA\Citra\load\mods\0004000000055D00\romfs\" -Force -Recurse
  Copy-Item -LiteralPath "temp\output\exefs\X\code.ips" -Destination "$env:APPDATA\Citra\load\mods\0004000000055D00\code.ips" -Force
}
if (Test-Path "$env:APPDATA\Citra\load\mods\0004000000055E00\romfs\") {
  Copy-Item -Path "temp\output\japanese\XY\*" -Destination "$env:APPDATA\Citra\load\mods\0004000000055E00\romfs\" -Force -Recurse
  Copy-Item -LiteralPath "temp\output\exefs\Y\code.ips" -Destination "$env:APPDATA\Citra\load\mods\0004000000055E00\code.ips" -Force
}
