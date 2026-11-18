$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Write-Host "=== Ecco the Dolphin: Automated Windows x64 Build ===" -ForegroundColor Cyan
$discEu = (Read-Host "1. Enter path to Europe disc image (.chd / .cue / .gdi) [REQUIRED]").Trim('"', "'", " ")
if (-not (Test-Path -LiteralPath $discEu)) { throw "Europe disc image not found: $discEu" }
$discRu = (Read-Host "2. Enter path to Paradox RUS disc image (.cdi / .chd / .gdi) [Optional, Enter to skip]").Trim('"', "'", " ")
$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
if ($vs) { cmd /c "`"$vs\VC\Auxiliary\Build\vcvars64.bat`" && set" | ForEach-Object { if ($_ -match "^([^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process") } } }
if (Test-Path "C:\Program Files\LLVM\bin") { $env:Path += ";C:\Program Files\LLVM\bin" }
$portSrc = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $portSrc
$dcDir = Join-Path $env:SystemDrive "EccoBuild\dreamcomp"
if (-not (Test-Path $dcDir)) { git clone -b linux-ecco --recurse-submodules https://github.com/cherryduck/dreamcomp.git $dcDir }
Push-Location $dcDir
if (-not (Test-Path ".venv")) { python -m venv .venv; .\.venv\Scripts\pip install -e "engine/tools/dcdisc[test]" pillow pygame }
$portLink = "ports\ecco-the-dolphin-defender-of-the-future-recomp"
New-Item -ItemType Directory -Force -Path "ports" | Out-Null
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
New-Item -ItemType Directory -Force -Path "$outDir\engine", "$outDir\disc", "$outDir\profiles\europe\dreamcomp\ecco", "$outDir\profiles\paradox_rus\dreamcomp\ecco" | Out-Null
Copy-Item "$portLink\build\game\ecco-the-dolphin-defender-of-the-future-recomp.exe" "$outDir\engine\" -Force
Copy-Item ".deps\SDL3-*\lib\x64\SDL3.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item ".deps\libchdr-build\chdr.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item "$portLink\game\ecco.toml", "$portLink\game\hud_overrides.ini" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $discEu -Destination "$outDir\disc\ecco_eu$([IO.Path]::GetExtension($discEu))" -Force
$ProgressPreference = "SilentlyContinue"; $ProgressPreference = "SilentlyContinue"; $z = "$env:TEMP\ecco_launcher.zip"
Invoke-WebRequest -Uri "https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.0-dc-pc-launcher/Ecco_the_Dolphin_DC_PC_Launcher_Win_Linux.zip" -OutFile $z
Expand-Archive -Path $z -DestinationPath $outDir -Force
Copy-Item "$PSScriptRoot\launcher.py" "$outDir\launcher.py" -Force
$ico = if (Test-Path -LiteralPath "$outDir\ecco.ico") { "$outDir\ecco.ico" } else { "$outDir\engine\ecco.ico" }
if (Test-Path -LiteralPath $ico) { $icoEsc = $ico.Replace("\", "\\"); "1 ICON `"$icoEsc`"" | Set-Content "$env:TEMP\ecco.rc" -Encoding ASCII; rc.exe /fo "$env:TEMP\ecco.res" "$env:TEMP\ecco.rc"; clang-cl /O2 /EHsc "$PSScriptRoot\ecco_stub.cpp" "$env:TEMP\ecco.res" /Fe:"$outDir\Ecco_the_Dolphin.exe" /link user32.lib shell32.lib /SUBSYSTEM:WINDOWS }
Write-Host "Checking Paradox RUS disc: [$discRu]" -ForegroundColor Cyan
if ($discRu -and (Test-Path -LiteralPath $discRu)) {
    if ($discRu.ToLower().EndsWith(".cdi") -and -not (Get-Command cdirip -ErrorAction SilentlyContinue)) {
        Write-Host "Fetching portable chdman.exe for .cdi extraction..." -ForegroundColor Cyan
        $chdDir = Join-Path $dcDir ".deps\chdman"
        $chdExe = Join-Path $chdDir "cdirip.exe"
        if (-not (Test-Path $chdExe)) {
            New-Item -ItemType Directory -Force -Path $chdDir | Out-Null
            $chdZip = "$env:TEMP\chdman_win64.zip"
            Invoke-WebRequest -Uri "https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.0-dc-pc-launcher/chdman_win64.zip" -OutFile $chdZip
            Expand-Archive -Path $chdZip -DestinationPath $chdDir -Force
            $found = Get-ChildItem $chdDir -Recurse -Filter "cdirip.exe" | Select-Object -First 1
            if ($found -and $found.FullName -ne $chdExe) { Copy-Item $found.FullName $chdExe -Force }
        }
        $env:Path = "$chdDir;$env:Path"
    }
    Write-Host "Extracting Paradox RUS translation & voiceover..." -ForegroundColor Cyan
    .\.venv\Scripts\python "$portSrc\tools\extract_paradox_mod.py" "$discRu" "$outDir\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox"
} else { Write-Host "Skipped Paradox RUS disc (Europe only)." -ForegroundColor Yellow }
Pop-Location
Write-Host "=== Build complete! Output folder: $outDir ===" -ForegroundColor Green
