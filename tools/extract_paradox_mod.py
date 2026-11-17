#!/usr/bin/env python3
import os, sys, fnmatch

PATTERNS = ("*.GDE", "*.GSG", "*.INP", "0GDTEX.PVR", "AUDIO64.DRV", "CONFIG.TXT", "MUSIC_*.AFS", "SOUND/*.KAT")

def extract_from_disc(disc_path, out_dir):
    from dcdisc.image import open_image
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    with open_image(disc_path) as img:
        for rel_path, data in img.walk_files():
            norm = rel_path.replace("\\", "/").lstrip("/")
            if any(fnmatch.fnmatch(norm.upper(), pat) for pat in PATTERNS):
                dst = os.path.join(out_dir, *norm.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(data)
                count += 1
    print(f"Extracted {count} Paradox RUS mod files into {out_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: extract_paradox_mod.py <paradox_disc_image> <output_mod_dir>")
    extract_from_disc(sys.argv[1], sys.argv[2])
