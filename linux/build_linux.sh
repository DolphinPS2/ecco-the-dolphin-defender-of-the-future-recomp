#!/usr/bin/env bash
set -euo pipefail

echo "=== Ecco the Dolphin: Automated Linux x64 Build (Etalon Layout) ==="
read -rp "1. Enter path to Europe disc image (.chd / .cue / .gdi) [REQUIRED]: " DISC_PATH
read -rp "2. Enter path to Paradox RUS disc image (.cdi / .chd / .gdi) [Optional]: " DISC_RU
if [[ ! -f "$DISC_PATH" ]]; then
    echo "Error: Disc image not found at $DISC_PATH" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
PORT_SRC="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$(dirname "$PORT_SRC")"
DC_DIR="$WORK_DIR/dreamcomp"

if [[ ! -d "$DC_DIR" ]]; then
    git clone -b linux-ecco --recurse-submodules https://github.com "$DC_DIR"
fi

cd "$DC_DIR"
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    .venv/bin/pip install -e "engine/tools/dcdisc[test]" pillow pygame
fi

mkdir -p ports
PORT_DST="ports/ecco-the-dolphin-defender-of-the-future-recomp"
rm -rf "$PORT_DST"
cp -a "$PORT_SRC" "$PORT_DST"

git -C "$DC_DIR" apply "$PORT_DST/patches/dreamcomp_ru_menu.patch" 2>/dev/null || true
.venv/bin/python tools/dc.py deps
.venv/bin/python tools/dc.py setup "$PORT_DST" --disc "$DISC_PATH"
rm -rf "$PORT_DST/build"
cmake -S "$PORT_DST" -B "$PORT_DST/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DDREAMCOMP_DIR="$DC_DIR" -DDREAMCOMP_FRONTEND=ON
.venv/bin/python tools/dc.py build "$PORT_DST"

OUT_DIR="$WORK_DIR/Ecco_the_Dolphin_PC"
mkdir -p "$OUT_DIR/engine" "$OUT_DIR/disc" "$OUT_DIR/profiles/europe/dreamcomp/ecco" "$OUT_DIR/profiles/paradox_rus/dreamcomp/ecco"
cp -f "$PORT_DST/build/game/ecco-the-dolphin-defender-of-the-future-recomp" "$OUT_DIR/engine/"
mkdir -p "$OUT_DIR/engine/frontend"
cp -f "$PORT_DST/frontend/lang_ru.ini" "$OUT_DIR/engine/frontend/lang_ru.ini"
if [[ -d "$PORT_DST/build/game/frontend" ]]; then
    cp -rf "$PORT_DST/build/game/frontend/." "$OUT_DIR/engine/frontend/"
fi
cp -f "$PORT_DST/game/ecco.toml" "$PORT_DST/game/hud_overrides.ini" "$OUT_DIR/engine/" 2>/dev/null || true
if [[ -d "$PORT_DST/game/extracted" ]]; then
    cp -a "$PORT_DST/game/extracted" "$OUT_DIR/engine/extracted"
fi
EXT="${DISC_PATH##*.}"
cp -f "$DISC_PATH" "$OUT_DIR/disc/ecco_eu.$EXT"

TMP_ZIP="/tmp/ecco_launcher.zip"
curl -fL "https://github.com" -o "$TMP_ZIP"
unzip -oq "$TMP_ZIP" -d "$OUT_DIR"
cp -f "$PORT_DST/windows/launcher.py" "$OUT_DIR/launcher.py"
chmod +x "$OUT_DIR/launcher.py" "$OUT_DIR/engine/ecco-the-dolphin-defender-of-the-future-recomp"

if [[ -n "${DISC_RU:-}" && -f "$DISC_RU" ]]; then
    .venv/bin/python "$PORT_DST/tools/extract_paradox_mod.py" "$DISC_RU" "$OUT_DIR/profiles/paradox_rus/dreamcomp/ecco/mods/rus_paradox"
fi

echo "=== Build complete! Output folder: $OUT_DIR ==="