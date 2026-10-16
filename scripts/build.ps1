param(
  [string[]]$games = @("XY", "ORAS")
)

if (Test-Path "temp") {
  Remove-Item -LiteralPath "temp" -Recurse -Force
}

$3dstool = "bin\3dstool\3dstool.exe"
$makerom = "bin\Project_CTR\makerom.exe"
$tool = "bin\PCTRGen6Tools\PCTRGen6Tools\bin\Release\net8.0-windows\win-x64\publish\PCTRGen6Tools.exe"

if (-not (Test-Path $tool)) {
  dotnet publish -c Release bin\PCTRGen6Tools\PCTRGen6Tools
}

$config = @{
  XY = @{
    titles = @("X", "Y")
    gametext = @("a\0\7\2", "a\0\7\3", "a\0\7\4")
    storytext = @("a\0\8\0", "a\0\8\1", "a\0\8\2")
  }
  ORAS = @{
    titles = @("OR", "AS")
    gametext = @("a\0\7\1", "a\0\7\2", "a\0\7\3")
    storytext = @("a\0\7\9", "a\0\8\0", "a\0\8\1")
  }
}

foreach ($game in $games) {
  $settings = $config[$game]
  if (-not (Test-Path "unpacked\japanese\$game\$($settings.gametext[0])")) {
    & $tool "export" -p "original_files\romfs\$game" -o "unpacked\japanese\$game"
  }

  python scripts/create_new_font.py $game
  python scripts/compile_exefs_patch.py $game

  & $tool "import-text" -p "unpacked\japanese\$game\$($settings.gametext[0])" -r "texts\$game\zh_Hans\gametext" -o "temp\import\japanese\$game\$($settings.gametext[0])"
  & $tool "import-text" -p "unpacked\japanese\$game\$($settings.gametext[1])" -r "texts\$game\zh_Hans\gametext" -o "temp\import\japanese\$game\$($settings.gametext[1])" -e "texts\$game\zh_Latn\gametext"
  & $tool "import-text" -p "unpacked\japanese\$game\$($settings.gametext[2])" -r "texts\$game\zh_Hans\gametext" -o "temp\import\japanese\$game\$($settings.gametext[2])" -e "texts\$game\zh_Hant\gametext"
  if ($game -eq "XY") {
    & $tool "import-text" -p "unpacked\japanese\XY\a\0\7\9" -r "texts\XY\ko\gametext" -o "temp\import\japanese\XY\a\0\7\9"
  }

  foreach ($path in $settings.storytext) {
    & $tool "import-text" -p "unpacked\japanese\$game\$path" -r "texts\$game\zh_Hans\storytext" -o "temp\import\japanese\$game\$path"
  }

  foreach ($archive in Get-ChildItem "files\images\$game\a\*\*\*" -Directory) {
    $path = "a\$($archive.Parent.Parent.Name)\$($archive.Parent.Name)\$($archive.Name)"
    & $tool "import-images" -p "unpacked\japanese\$game\$path" -r "files\images\$game\$path" -o "temp\import\japanese\$game\$path"
  }

  & $tool "import" -p "original_files\romfs\$game" -r "temp\import\japanese\$game" -o "temp\output\japanese\$game"

  foreach ($title in $settings.titles) {
    $work = "temp\build_patches\$title"
    New-Item -ItemType Directory -Path "$work\exefs", "$work\romfs", "$work\banner" -Force | Out-Null
    & $3dstool -x -t banner -f "original_files\exefs\$title\banner.bnr" --banner-dir "$work\banner"
    & $tool "import-banner" -p "$work\banner" -r "files\banners\$title" -o "$work\banner"
    Copy-Item -LiteralPath "original_files\exefs\$title\exefs_header.bin" -Destination "$work\exefs_header.bin" -Force
    & $3dstool -c -t banner -f "$work\exefs\banner.bnr" --banner-dir "$work\banner"
    Copy-Item -LiteralPath "original_files\exefs\$title\header.bin", "original_files\exefs\$title\exheader.bin", "original_files\exefs\$title\logo.bin", "original_files\exefs\$title\plain.bin", "original_files\exefs\$title\title.tmd" -Destination $work -Force
    Copy-Item -LiteralPath "original_files\exefs\$title\icon.icn" -Destination "$work\exefs\icon.icn" -Force
    Copy-Item -Path "original_files\romfs\$game\*" -Destination "$work\romfs" -Recurse -Force
    Copy-Item -Path "original_files\romfs\$title\*" -Destination "$work\romfs" -Recurse -Force
    $metadata = python scripts/build_patches.py metadata $title $work | ConvertFrom-Json

    $luma = "out\luma\titles\$($metadata.base_title_id)"
    New-Item -ItemType Directory -Path "$luma\romfs" -Force | Out-Null
    Copy-Item -Path "temp\output\japanese\$game\*" -Destination "$luma\romfs" -Recurse -Force
    Copy-Item -LiteralPath "temp\output\exefs\$title\code.ips" -Destination "$luma\code.ips" -Force
    Copy-Item -Path "$luma\romfs\*" -Destination "$work\romfs" -Recurse -Force

    python scripts/build_patches.py code $title $work
    & $3dstool -z -f "$work\code.bin" --compress-type blz --compress-out "$work\exefs\code.bin"
    & $3dstool -c -t exefs -f "$work\translated_exefs.bin" --header "$work\exefs_header.bin" --exefs-dir "$work\exefs"
    & $3dstool -c -t romfs -f "$work\translated_romfs.bin" --romfs-dir "$work\romfs"
    & $3dstool -c -t cxi -f "$work\translated.cxi" --not-encrypt --header "$work\header.bin" --exh "$work\exheader.bin" --logo "$work\logo.bin" --plain "$work\plain.bin" --exefs "$work\translated_exefs.bin" --romfs "$work\translated_romfs.bin"
    New-Item -ItemType Directory -Path "out\cia" -Force | Out-Null
    & $makerom -f cia -o "out\cia\$($metadata.title_id).cia" -content "$work\translated.cxi:$($metadata.content_index):0x$($metadata.content_id)" -ver $metadata.title_version -ignoresign

    $citra = "$env:APPDATA\Citra\load\mods\$($metadata.base_title_id)"
    if (Test-Path "$citra\romfs\") {
      Copy-Item -Path "temp\output\japanese\$game\*" -Destination "$citra\romfs\" -Force -Recurse
      Copy-Item -LiteralPath "temp\output\exefs\$title\code.ips" -Destination "$citra\code.ips" -Force
    }
  }
}
