param(
    [string]$DiscEu = "",
    [string]$DiscRu = ""
)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Write-Host "=== Ecco the Dolphin: Automated Windows x64 Build (Etalon Layout) ===" -ForegroundColor Cyan

if (-not $DiscEu) { $DiscEu = Read-Host "1. Enter path to Europe disc image (.chd / .cue / .gdi) [REQUIRED]" }
$discEu = $DiscEu.Trim().Trim('"') -replace '^\d+\.\s*', ''
if (-not (Test-Path $discEu)) { throw "Europe disc image not found: $discEu" }

if (-not $DiscRu) { $DiscRu = Read-Host "2. Enter path to Paradox RUS disc image (.cdi / .chd / .gdi) [Optional, press Enter to skip]" }
$discRu = ""
if ($DiscRu) {
    $discRu = $DiscRu.Trim().Trim('"') -replace '^\d+\.\s*', ''
    if ($discRu -and -not (Test-Path $discRu)) { throw "Paradox RUS disc image not found: $discRu" }
}

$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
if ($vs) {
    cmd /c "`"$vs\VC\Auxiliary\Build\vcvars64.bat`" && set" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable($matches, $matches, "Process") }
    }
}
if (Test-Path "C:\Program Files\LLVM\bin") { $env:Path += ";C:\Program Files\LLVM\bin" }

$portSrc = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $portSrc
$dcDir = Join-Path $env:SystemDrive "EccoBuild\dreamcomp"
if (-not (Test-Path $dcDir)) {
    git clone -b linux-ecco --recurse-submodules https://github.com $dcDir
}

Push-Location $dcDir
if (-not (Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\pip install -q -e "engine/tools/dcdisc[test]" pillow pygame

$portLink = "ports\ecco-the-dolphin-defender-of-the-future-recomp"
New-Item -ItemType Directory -Force -Path "ports" | Out-Null
Remove-Item $portLink -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item $portSrc $portLink -Recurse -Force

cmake -S engine/third_party/libchdr -B .deps/libchdr-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON
cmake --build .deps/libchdr-build
$env:DCDISC_LIBCHDR = (Resolve-Path ".deps\libchdr-build\chdr.dll").Path
.\.venv\Scripts\python tools/dc.py deps
.\.venv\Scripts\python tools/dc.py setup $portLink --disc "$discEu"
Remove-Item "$portLink\build" -Recurse -Force -ErrorAction SilentlyContinue
cmake -S $portLink -B "$portLink\build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DDREAMCOMP_DIR="$dcDir" -DDREAMCOMP_FRONTEND=OFF
.\.venv\Scripts\python tools/dc.py build $portLink

$outDir = Join-Path $root "Ecco_the_Dolphin_Windows"
New-Item -ItemType Directory -Force -Path "$outDir\engine", "$outDir\disc", "$outDir\runtime", "$outDir\profiles\europe\dreamcomp\ecco", "$outDir\profiles\paradox_rus\dreamcomp\ecco" | Out-Null

# 1. Р В РІР‚СњР В Р вЂ Р В РЎвЂР В Р’В¶Р В РЎвЂўР В РЎвЂќ, DLL, Р В РЎвЂќР В РЎвЂўР В Р вЂ¦Р РЋРІР‚С›Р В РЎвЂР В РЎвЂ“Р В РЎвЂ Р В РЎвЂ Р В РЎвЂўР В Р’В±Р РЋР РЏР В Р’В·Р В Р’В°Р РЋРІР‚С™Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ extracted\fs\1ST_READ.BIN
Copy-Item "$portLink\build\game\ecco-the-dolphin-defender-of-the-future-recomp.exe" "$outDir\engine\" -Force
Copy-Item ".deps\SDL3-*\lib\x64\SDL3.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item ".deps\libchdr-build\chdr.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item "$portLink\game\ecco.toml", "$portLink\game\hud_overrides.ini" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
if (Test-Path "$portLink\game\extracted") {
    Copy-Item "$portLink\game\extracted" "$outDir\engine\extracted" -Recurse -Force
}

# 2. Р В РЎвЂєР В Р’В±Р РЋР вЂљР В Р’В°Р В Р’В· Р В Р’ВµР В Р вЂ Р РЋР вЂљР В РЎвЂўР В РЎвЂ”Р В Р’ВµР В РІвЂћвЂ“Р РЋР С“Р В РЎвЂќР В РЎвЂўР В РЎвЂ“Р В РЎвЂў Р В РўвЂР В РЎвЂР РЋР С“Р В РЎвЂќР В Р’В°
$discExt = [IO.Path]::GetExtension($discEu)
Copy-Item "$discEu" "$outDir\disc\ecco_eu$discExt" -Force

# 3. Р В РЎС™Р В Р’ВµР В РўвЂР В РЎвЂР В Р’В°Р РЋРІР‚С›Р В Р’В°Р В РІвЂћвЂ“Р В Р’В»Р РЋРІР‚в„– 2K-Р В Р’В»Р В Р’В°Р РЋРЎвЂњР В Р вЂ¦Р РЋРІР‚РЋР В Р’ВµР РЋР вЂљР В Р’В°, Р РЋР С“Р В РЎвЂќР РЋР вЂљР В РЎвЂР В РЎвЂ”Р РЋРІР‚С™ Р В РЎвЂ Р В РЎвЂР В РЎвЂќР В РЎвЂўР В Р вЂ¦Р В РЎвЂќР В Р’В°
if (Test-Path "$portSrc\media") { Copy-Item "$portSrc\media" "$outDir\media" -Recurse -Force }
Copy-Item "$PSScriptRoot\launcher.py" "$outDir\launcher.py" -Force
Copy-Item "$PSScriptRoot\ecco.ico", "$PSScriptRoot\ecco_icon.png" "$outDir\engine\" -Force -ErrorAction SilentlyContinue

# 4. Р В РЎСљР В Р’В°Р РЋРІР‚С™Р В РЎвЂР В Р вЂ Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ Ecco_the_Dolphin.exe Р РЋР С“ Р В РЎвЂР В РЎвЂќР В РЎвЂўР В Р вЂ¦Р В РЎвЂќР В РЎвЂўР В РІвЂћвЂ“ Р В РўвЂР В Р’ВµР В Р’В»Р РЋР Р‰Р РЋРІР‚С›Р В РЎвЂР В Р вЂ¦Р В Р’В°
[System.IO.File]::WriteAllText("$env:TEMP\ecco.rc", '1 ICON "ecco.ico"', [System.Text.Encoding]::ASCII)
llvm-rc /I "$PSScriptRoot" /FO "$env:TEMP\ecco.res" "$env:TEMP\ecco.rc"
clang-cl /O2 /EHsc "$PSScriptRoot\ecco_stub.cpp" "$env:TEMP\ecco.res" /Fe:"$outDir\Ecco_the_Dolphin.exe" /link user32.lib shell32.lib /SUBSYSTEM:WINDOWS

# 5. Р В РЎвЂ™Р В Р вЂ Р РЋРІР‚С™Р В РЎвЂўР В Р вЂ¦Р В РЎвЂўР В РЎВР В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ runtime (ffmpeg/ffplay Р В РЎвЂР В Р’В· Р РЋР С“Р В РЎвЂР РЋР С“Р РЋРІР‚С™Р В Р’ВµР В РЎВР РЋРІР‚в„– Р В РЎвЂР В Р’В»Р В РЎвЂ Р В РЎвЂР В Р’В· Р РЋР С“Р В РЎвЂўР РЋР С“Р В Р’ВµР В РўвЂР В Р вЂ¦Р В Р’ВµР В РІвЂћвЂ“ Р РЋР РЉР РЋРІР‚С™Р В Р’В°Р В Р’В»Р В РЎвЂўР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В РІвЂћвЂ“ Р РЋР С“Р В Р’В±Р В РЎвЂўР РЋР вЂљР В РЎвЂќР В РЎвЂ)
foreach ($tool in @("ffmpeg.exe", "ffplay.exe")) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) { Copy-Item $cmd.Source "$outDir\runtime\$tool" -Force }
}
if (-not (Test-Path "$outDir\runtime\ffmpeg.exe")) {
    Write-Host "Downloading portable ffmpeg.exe for 2K launcher..." -ForegroundColor Cyan
    $ffZip = "$env:TEMP\ffmpeg_win64.zip"
    curl.exe -L -s "https://gyan.dev" -o "$ffZip"
    if (Test-Path $ffZip) {
        Expand-Archive -Path $ffZip -DestinationPath "$env:TEMP\ff_ext" -Force
        $ffBin = Get-ChildItem "$env:TEMP\ff_ext" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        if ($ffBin) { Copy-Item $ffBin.FullName "$outDir\runtime\ffmpeg.exe" -Force }
    }
}

# 6. Р В РІР‚ВР В Р’В°Р РЋРІР‚С™Р В Р вЂ¦Р В РЎвЂР В РЎвЂќР В РЎвЂ Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р В РЎвЂќР В Р’В° (Р РЋРІР‚С™Р В РЎвЂўР РЋРІР‚РЋР В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В РЎвЂќР В РЎвЂўР В РЎвЂ”Р В РЎвЂР В РЎвЂ Р РЋР РЉР РЋРІР‚С™Р В Р’В°Р В Р’В»Р В РЎвЂўР В Р вЂ¦Р В Р’В°)
Set-Content "$outDir\Start_Launcher.bat" "@echo off`r`ncd /d ""%~dp0""`r`nif exist ""runtime\pythonw.exe"" (start """" ""runtime\pythonw.exe"" ""launcher.py"") else if exist ""C:\EccoBuild\dreamcomp\.venv\Scripts\pythonw.exe"" (start """" ""C:\EccoBuild\dreamcomp\.venv\Scripts\pythonw.exe"" ""launcher.py"") else (start """" pythonw ""launcher.py"")" -Encoding ASCII
Set-Content "$outDir\Play_Europe.bat" "@echo off`r`ncd /d ""%~dp0engine""`r`nset ""APPDATA=%~dp0profiles\europe""`r`necco-the-dolphin-defender-of-the-future-recomp.exe --config ""%~dp0engine\ecco.toml"" --disc ""%~dp0disc\ecco_eu$discExt"" --window" -Encoding ASCII
Set-Content "$outDir\Play_Paradox_RUS.bat" "@echo off`r`ncd /d ""%~dp0engine""`r`nset ""APPDATA=%~dp0profiles\paradox_rus""`r`necco-the-dolphin-defender-of-the-future-recomp.exe --config ""%~dp0engine\ecco.toml"" --disc ""%~dp0disc\ecco_eu$discExt"" --window" -Encoding ASCII

# 7. Р В Р’В Р В Р’В°Р РЋР С“Р В РЎвЂ”Р В Р’В°Р В РЎвЂќР В РЎвЂўР В Р вЂ Р В РЎвЂќР В Р’В° 131 Р РЋРІР‚С›Р В Р’В°Р В РІвЂћвЂ“Р В Р’В»Р В Р’В° Paradox RUS (96 + 35 SOUND) Р В РЎвЂ Р РЋР С“Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ settings.ini
if ($discRu) {
    Write-Host "Extracting Paradox RUS translation & voiceover..." -ForegroundColor Cyan
    .\.venv\Scripts\python "$portSrc\tools\extract_paradox_mod.py" "$discRu" "$outDir\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox"
} else {
    Write-Host "Skipped Paradox RUS disc (Europe only)." -ForegroundColor Yellow
}

Pop-Location
Write-Host "=== Build complete! Output folder: $outDir ===" -ForegroundColor Green