$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

if (-not (Test-Path "unpacked\japanese\ORAS_Demo\a\0\7\1")) {
  & $tool "export" -p "original_files\japanese\ORAS_Demo" -o "unpacked\japanese\ORAS_Demo"
}

& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\7\1" -r "texts\ORAS_Demo\zh_Hans\gametext" -o "temp\import\japanese\ORAS_Demo\a\0\7\1"
& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\7\2" -r "texts\ORAS_Demo\zh_Hans\gametext" -o "temp\import\japanese\ORAS_Demo\a\0\7\2" -e "texts\ORAS_Demo\zh_Latn\gametext"
& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\7\3" -r "texts\ORAS_Demo\zh_Hans\gametext" -o "temp\import\japanese\ORAS_Demo\a\0\7\3" -e "texts\ORAS_Demo\zh_Hant\gametext"

& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\7\9" -r "texts\ORAS_Demo\zh_Hans\storytext" -o "temp\import\japanese\ORAS_Demo\a\0\7\9"
& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\8\0" -r "texts\ORAS_Demo\zh_Hans\storytext" -o "temp\import\japanese\ORAS_Demo\a\0\8\0"
& $tool "import-text" -p "unpacked\japanese\ORAS_Demo\a\0\8\1" -r "texts\ORAS_Demo\zh_Hans\storytext" -o "temp\import\japanese\ORAS_Demo\a\0\8\1"

& $tool "import" -p "original_files\japanese\ORAS_Demo" -r "temp\import\japanese\ORAS_Demo" -o "temp\output\japanese\ORAS_Demo"

if (Test-Path "$env:APPDATA\Citra\load\mods\000400000014A300\romfs\") {
  Copy-Item -Path "temp\output\japanese\ORAS_Demo\*" -Destination "$env:APPDATA\Citra\load\mods\000400000014A300\romfs\" -Force -Recurse
}