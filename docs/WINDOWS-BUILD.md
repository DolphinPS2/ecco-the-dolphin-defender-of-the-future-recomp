# Building & Packaging on Windows x64

Tested and verified on **Windows 10 / 11 x64** using **Visual Studio 2022 Build Tools** (`vcvars64.bat`), **LLVM `clang-cl`**, **Ninja**, **CMake**, **Vulkan SDK**, and **Python 3.12**.

## Prerequisites

1. **Visual Studio 2022** (or Build Tools) with **Desktop development with C++** (required for Windows SDK headers, `rc.exe`, and `ml64.exe`).
2. **LLVM / Clang** (`winget install LLVM.LLVM`) — recommended for fast multi-shard compilation via `clang-cl`.
3. **CMake & Ninja** (`winget install Kitware.CMake Ninja-build.Ninja`).
4. **Vulkan SDK** (`winget install KhronosGroup.VulkanSDK`) — provides Vulkan headers and `glslc.exe`.
5. **Python 3.12+** (`winget install Python.Python.3.12`).
6. *(Optional, for GUI launcher & installer)* **FFmpeg** (`winget install Gyan.FFmpeg`) and **Inno Setup 6** (`winget install JRSoftware.InnoSetup`).

## Step-by-Step Build (PowerShell)

Open PowerShell and run:

```powershell
\$env:PYTHONUTF8 = "1"

# 1. Initialize MSVC x64 environment (required for Windows SDK & ml64.exe)
\(vs = & "\){env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -property installationPath
cmd /c "`"$vs\VC\Auxiliary\Build\vcvars64.bat`" && set" | ForEach-Object {
    if (\(_ -match "^([^=]+)=(.*)\)") {
        [Environment]::SetEnvironmentVariable(\(matches[1],\)matches[2], "Process")
    }
}
\$env:Path += ";C:\Program Files\LLVM\bin"

# 2. Clone dreamcomp (linux-ecco branch!) and this port
git clone -b linux-ecco --recurse-submodules https://github.com
cd dreamcomp
python -m venv .venv
.\.venv\Scripts\pip install -e "engine/tools/dcdisc[test]" pillow

git clone https://github.com ports\ecco-the-dolphin-defender-of-the-future-recomp
\$P = "ports/ecco-the-dolphin-defender-of-the-future-recomp"

# 3. Setup disc (extracts 0.BIN boot executable only; supports .cue/.bin, .gdi, .chd)
.\.venv\Scripts\python tools/dc.py setup \$P --disc "D:\Games\Ecco the Dolphin - Defender of the Future (Europe) (En,Fr,De,Es).chd"

# 4. Build native Windows executable
.\.venv\Scripts\python tools/dc.py build \$P

# 5. Run with DXGI presentation path
.\.venv\Scripts\python tools/dc.py run \$P --window --present-path dxgi
```

## Critical Build Traps & Fixes Discovered on Windows

### Trap W1 — CMake Hangs / Stalls During Font Download (`Inter` / `PromptFont`)
- **Symptom:** CMake configuration appears completely frozen with no progress output right after configuring submodules.
- **Cause:** `DreamcompFrontend.cmake` attempts to download external UI fonts (`Inter` and `PromptFont`) over HTTPS during CMake configure time without a short timeout. If CDN access is throttled, blocked, or stalled by TLS/proxy settings, CMake waits indefinitely.
- **Fix:**
  - Either pre-populate the font files in the CMake download cache / `build/_deps` directory before running `dc.py build`, **or**
  - Configure with `-DDREAMCOMP_FRONTEND=OFF` when pairing the engine binary with a standalone launcher (`windows/launcher.py`).

### Trap W2 — Compiler Hang / Out-of-Memory Without `linux-ecco` Sharding
- **Symptom:** Compiling the generated C++ code freezes the system or exhausts RAM/pagefile.
- **Cause:** Building against upstream `danielgomesvieira2000/dreamcomp` (`main`) emits all **17,574 recompiled SH-4 functions** into a single monolithic `.cpp` translation unit.
- **Fix:** Always use the **`linux-ecco`** branch of `cherryduck/dreamcomp`, which splits generated code across CPU threads (`DREAM_GEN_SHARDS`), keeping memory usage low and finishing compilation in ~1–2 minutes.

### Trap W3 — `.chd` Setup Fails Without `ml64.exe` (`libchdr` / `chdr.dll`) or `PYTHONUTF8=1`
- **Symptom:** `dc.py setup` fails to extract `.chd` disc images because `chdr.dll` failed to build, or Python raises `UnicodeDecodeError` (`cp1251`) on non-English Windows locales.
- **Fix:** Always import `vcvars64.bat` into PowerShell before building (so CMake finds `ml64.exe` for `libchdr` assembly routines) and set `$env:PYTHONUTF8 = "1"`.

### Trap W4 — Portable Windows Launcher & Console Window Suppression
- **Details:** See `windows/launcher.py`, `windows/ecco_stub.cpp`, and `windows/ecco_setup.iss`:
  - **Profile Isolation:** Passing `APPDATA=<profile_dir>` isolates VMU saves (`vmu_a1.bin`), `settings.ini`, and `mods/` per profile (e.g., original Europe release vs. localized/modded profiles) without touching `%APPDATA%\dreamcomp`.
  - **No Console Popups:** App execution aliases created by `winget` (`WinGet\Links\ffmpeg.exe`) ignore Python's `CREATE_NO_WINDOW` flag and spawn visible console windows. Bundle or point directly to the real `ffmpeg.exe` / `ffplay.exe` binaries and compile `windows/ecco_stub.cpp` with `/SUBSYSTEM:WINDOWS`.
  - **Display Presentation:** Pass `--present-path dxgi` on Windows for low-latency fullscreen presentation.
