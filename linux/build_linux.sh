#!/usr/bin/env bash
set -euo pipefail

echo "=== Ecco the Dolphin: Automated Linux x64 Build ==="
read -rp "Enter full path to your Ecco Europe disc image (.chd / .cue / .gdi): " DISC_PATH
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
    .venv/bin/pip install -e "engine/tools/dcdisc[test]" pillow
fi

mkdir -p ports
PORT_DST="ports/ecco-the-dolphin-defender-of-the-future-recomp"
rm -rf "$PORT_DST"
cp -a "$PORT_SRC" "$PORT_DST"

.venv/bin/python tools/dc.py setup "$PORT_DST" --disc "$DISC_PATH"
# Pass -DDREAMCOMP_FRONTEND=OFF if CMake hangs while downloading Inter/PromptFont fonts
CMAKE_ARGS="${CMAKE_ARGS:-}" .venv/bin/python tools/dc.py build "$PORT_DST"

echo "=== Build complete! Run with: $DC_DIR/.venv/bin/python $DC_DIR/tools/dc.py run $PORT_DST --window ==="
