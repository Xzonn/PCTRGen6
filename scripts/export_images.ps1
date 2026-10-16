$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

foreach ($game in @("XY", "ORAS")) {
  & $tool "export" -p "original_files\romfs\$game" -o "unpacked\japanese\$game"
}

& $tool "export-images" -p "unpacked\japanese" -o "maintenance\images"
