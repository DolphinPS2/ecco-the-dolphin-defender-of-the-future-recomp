$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Write-Host "=== Ecco the Dolphin: Automated Windows x64 Build ===" -ForegroundColor Cyan
$disc = Read-Host "Enter full path to your Ecco Europe disc image (.chd / .cue / .gdi)"
if (-not (Test-Path $disc)) { throw "Disc image not found: $disc" }

$vs = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
if ($vs) {
    cmd /c "`"$vs\VC\Auxiliary\Build\vcvars64.bat`" && set" | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable($matches, $matches, "Process") }
    }
}
if (Test-Path "C:\Program Files\LLVM\bin") { $env:Path += ";C:\Program Files\LLVM\bin" }

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$dcDir = Join-Path $root "dreamcomp"
if (-not (Test-Path $dcDir)) {
    git clone -b linux-ecco --recurse-submodules https://github.com $dcDir
}
Push-Location $dcDir
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\pip install -e "engine/tools/dcdisc[test]" pillow
}
$portLink = "ports\ecco-the-dolphin-defender-of-the-future-recomp"
if (-not (Test-Path $portLink)) {
    New-Item -ItemType Directory -Force -Path "ports" | Out-Null
    Copy-Item (Split-Path -Parent $PSScriptRoot) $portLink -Recurse -Force
}
.\.venv\Scripts\python tools/dc.py setup $portLink --disc "$disc"
.\.venv\Scripts\python tools/dc.py build $portLink
Pop-Location
Write-Host "=== Build complete! Executable is inside dreamcomp\$portLink\build\game ===" -ForegroundColor Green
