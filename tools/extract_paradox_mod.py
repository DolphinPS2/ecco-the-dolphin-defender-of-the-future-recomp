import os, sys, shutil, tempfile, subprocess, fnmatch

PATTERNS = ("*.GDE", "*.GSG", "*.INP", "0GDTEX.PVR", "AUDIO64.DRV", "CONFIG.TXT", "MUSIC_*.AFS", "SOUND/*.KAT")

def match_name(rel_path):
    head, _, _ = rel_path.replace("\\", "/").lstrip("/").partition(";")
    return head if any(fnmatch.fnmatch(head.upper(), p) for p in PATTERNS) else None

def extract_from_disc(disc_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    tmp_chd = None
    src = disc_path
    if disc_path.lower().endswith(".cdi"):
        chdman = shutil.which("chdman")
        if not chdman:
            raise RuntimeError("To extract a .cdi image, place chdman.exe in PATH or convert the .cdi to .chd/.gdi first.")
        tmp_chd = os.path.join(tempfile.gettempdir(), "ecco_paradox_tmp.chd")
        subprocess.run([chdman, "createcd", "-i", disc_path, "-o", tmp_chd, "-f"], check=True)
        src = tmp_chd
    try:
        from dcdisc.image import open_image
        count = 0
        with open_image(src) as img:
            for rel_path, data in img.walk_files():
                matched = match_name(rel_path)
                if matched:
                    dst = os.path.join(out_dir, *matched.split("/"))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(dst, "wb") as f:
                        f.write(data)
                    count += 1
    finally:
        if tmp_chd and os.path.exists(tmp_chd):
            os.remove(tmp_chd)
    cfg = os.path.join(os.path.dirname(os.path.dirname(out_dir)), "settings.ini")
    with open(cfg, "w", encoding="utf-8") as sf:
        sf.write("mods = rus_paradox\n")
    print(f"Extracted {count} Paradox RUS mod files into {out_dir}")

if __name__ == "__main__":
    _, src, dst = sys.argv
    extract_from_disc(src, dst)