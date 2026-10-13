$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

if (-not (Test-Path "unpacked\japanese\ORAS\a\0\7\1")) {
  & $tool "export" -p "original_files\japanese\ORAS" -o "unpacked\japanese\ORAS"
}

& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\7\1" -r "texts\ORAS\zh_Hans\gametext" -o "temp\import\japanese\ORAS\a\0\7\1"
& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\7\2" -r "texts\ORAS\zh_Hans\gametext" -o "temp\import\japanese\ORAS\a\0\7\2" -e "texts\ORAS\zh_Latn\gametext"
& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\7\3" -r "texts\ORAS\zh_Hans\gametext" -o "temp\import\japanese\ORAS\a\0\7\3" -e "texts\ORAS\zh_Hant\gametext"

& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\7\9" -r "texts\ORAS\zh_Hans\storytext" -o "temp\import\japanese\ORAS\a\0\7\9"
& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\8\0" -r "texts\ORAS\zh_Hans\storytext" -o "temp\import\japanese\ORAS\a\0\8\0"
& $tool "import-text" -p "unpacked\japanese\ORAS\a\0\8\1" -r "texts\ORAS\zh_Hans\storytext" -o "temp\import\japanese\ORAS\a\0\8\1"

& $tool "import" -p "original_files\japanese\ORAS" -r "temp\import\japanese\ORAS" -o "temp\output\japanese\ORAS"

if (Test-Path "$env:APPDATA\Citra\load\mods\000400000011C400\romfs\") {
  Copy-Item -Path "temp\output\japanese\ORAS\*" -Destination "$env:APPDATA\Citra\load\mods\000400000011C400\romfs\" -Force -Recurse
}
if (Test-Path "$env:APPDATA\Citra\load\mods\000400000011C500\romfs\") {
  Copy-Item -Path "temp\output\japanese\ORAS\*" -Destination "$env:APPDATA\Citra\load\mods\000400000011C500\romfs\" -Force -Recurse
}
