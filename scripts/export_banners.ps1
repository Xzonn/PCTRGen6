$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

foreach ($title in @("X", "Y", "OR", "AS")) {
  $work = "temp\build_patches\$title"
  New-Item -ItemType Directory -Path "$work\banner" -Force | Out-Null
  & "bin\3dstool\3dstool.exe" -x -t banner -f "original_files\exefs\$title\banner.bnr" --banner-dir "$work\banner"
  & $tool "export-banner" -p "$work\banner" -o "maintenance\banners\$title"
}
