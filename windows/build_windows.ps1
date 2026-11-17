$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Write-Host "=== Ecco the Dolphin: Automated Windows x64 Build ===" -ForegroundColor Cyan
$discEu = Read-Host "1. Enter path to Europe disc image (.chd / .cue / .gdi) [REQUIRED]"
if (-not (Test-Path $discEu)) { throw "Europe disc image not found: $discEu" }
$discRu = Read-Host "2. Enter path to Paradox RUS disc image (.cdi / .chd / .gdi) [Optional, press Enter to skip]"

$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
if ($vs) {
    cmd /c "`"$vs\VC\Auxiliary\Build\vcvars64.bat`" && set" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process") }
    }
}
if (Test-Path "C:\Program Files\LLVM\bin") { $env:Path += ";C:\Program Files\LLVM\bin" }

$portSrc = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $portSrc
$dcDir = Join-Path $root "dreamcomp"
if (-not (Test-Path $dcDir)) {
    git clone -b linux-ecco --recurse-submodules https://github.com $dcDir
}
Push-Location $dcDir
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -e "engine/tools/dcdisc[test]" pillow pygame
}
$portLink = "ports\ecco-the-dolphin-defender-of-the-future-recomp"
New-Item -ItemType Directory -Force -Path "ports" | Out-Null
Copy-Item $portSrc $portLink -Recurse -Force

.\.venv\Scripts\python tools/dc.py setup $portLink --disc "$discEu"
.\.venv\Scripts\python tools/dc.py build $portLink
if ($discRu -and (Test-Path $discRu)) { .\.venv\Scripts\python "$portLink\tools\extract_paradox_mod.py" "$discRu" "$root\Ecco_the_Dolphin_Windows\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox" }

$outDir = Join-Path $root "Ecco_the_Dolphin_Windows"
New-Item -ItemType Directory -Force -Path "$outDir\engine", "$outDir\disc", "$outDir\profiles\europe\dreamcomp\ecco", "$outDir\profiles\paradox_rus\dreamcomp\ecco" | Out-Null
Copy-Item "$portLink\build\game\ecco-the-dolphin-defender-of-the-future-recomp.exe" "$outDir\engine\" -Force
Copy-Item ".deps\SDL3-*\lib\x64\SDL3.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item ".deps\libchdr-build\chdr.dll" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item "$portLink\game\ecco.toml", "$portLink\game\hud_overrides.ini" "$outDir\engine\" -Force -ErrorAction SilentlyContinue
Copy-Item "$discEu" "$outDir\disc\ecco_eu$([IO.Path]::GetExtension($discEu))" -Force
$z = "$env:TEMP\ecco_launcher.zip"; Invoke-WebRequest -Uri "https://github.com" -OutFile $z; Expand-Archive -Path $z -DestinationPath "$root\Ecco_the_Dolphin_Windows" -Force; Copy-Item "$PSScriptRoot\launcher.py" "$outDir\launcher.py" -Force
if (Test-Path "$portSrc\media") { Copy-Item "$portSrc\media" "$outDir\media" -Recurse -Force }
if ($discRu -and (Test-Path $discRu)) {
    .\.venv\Scripts\python "$PSScriptRoot\..\tools\extract_paradox_mod.py" "$discRu" "$outDir\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox"
}
Pop-Location
Write-Host "=== Build complete! Output folder: $outDir ===" -ForegroundColor Green

