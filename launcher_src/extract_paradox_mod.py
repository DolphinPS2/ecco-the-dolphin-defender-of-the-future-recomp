# -*- coding: utf-8 -*-
import os, sys, struct, shutil, tempfile, subprocess

def clean_iso_name(raw):
    idx = raw.find(";")
    s = raw[:idx] if idx != -1 else raw
    s = s.strip()
    return None if (not s or s in ("\x00", "\x01")) else s

def extract_cdi_native(cdi_path, out_dir, on_progress=None):
    with open(cdi_path, "rb") as f:
        d = f.read()
    pvd_off = d.rfind(b"\x01CD001\x01")
    if pvd_off < 0:
        raise RuntimeError("PVD не найден в CDI")
    sec = 2336 if (pvd_off - 8) % 2336 == 0 or (pvd_off % 2336 != 0 and (pvd_off - 16) % 2352 != 0) else 2352
    s2_base = pvd_off - 16 * sec
    tscr_off = d.find(b"TSCR\x10\x00\x04\x00PVRT")
    s1_base = (tscr_off - 25 * sec) if tscr_off >= 0 else 0
    root_off = pvd_off + 4 * sec
    pvd = d[pvd_off : pvd_off + 2048]
    root_size = int.from_bytes(pvd[166:170], "little")
    buf_root = b"".join(d[root_off + i * sec : root_off + i * sec + 2048] for i in range((root_size + 2047) // 2048))
    s2_start_lba = 385099
    pos = 0
    while pos < root_size:
        rl = buf_root[pos]
        if rl == 0:
            pos = ((pos // 2048) + 1) * 2048
            continue
        nl = buf_root[pos + 32]
        nm = clean_iso_name(buf_root[pos + 33 : pos + 33 + nl].decode("ascii", "ignore"))
        if nm == "0.BIN":
            bin_lba = int.from_bytes(buf_root[pos + 2 : pos + 6], "little")
            bin_off = d.find(b"\x00\x07\xff\x0f\x00\x12/1122")
            if bin_off > s2_base:
                s2_start_lba = bin_lba - ((bin_off - s2_base) // sec)
            break
        pos += rl

    def read_sec(lba):
        off = (s2_base + (lba - s2_start_lba) * sec) if lba >= s2_start_lba else (s1_base + lba * sec)
        return d[off : off + 2048]

    items = []
    pos = 0
    while pos < root_size:
        rl = buf_root[pos]
        if rl == 0:
            pos = ((pos // 2048) + 1) * 2048
            continue
        flba = int.from_bytes(buf_root[pos + 2 : pos + 6], "little")
        fsz = int.from_bytes(buf_root[pos + 10 : pos + 14], "little")
        flags = buf_root[pos + 25]
        nl = buf_root[pos + 32]
        nm = clean_iso_name(buf_root[pos + 33 : pos + 33 + nl].decode("ascii", "ignore"))
        if nm and nm.upper().endswith(".GDE") and not (flags & 2):
            items.append((nm, flba, fsz))
        pos += rl

    total = len(items)
    for idx, (nm, flba, fsz) in enumerate(items, 1):
        with open(os.path.join(out_dir, nm), "wb") as wf:
            rem, s = fsz, flba
            while rem > 0:
                ch = read_sec(s)[: min(2048, rem)]
                wf.write(ch)
                rem -= len(ch)
                s += 1
        if on_progress:
            on_progress(idx, total, nm)
    return total

def extract_gdi_native(gdi_path, out_dir, on_progress=None):
    base_dir = os.path.dirname(os.path.abspath(gdi_path))
    tracks = []
    for line in open(gdi_path, "r", encoding="utf-8", errors="ignore").read().splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 5:
            lba, sec_sz, fname = int(parts[1]), int(parts[3]), parts[4].strip('"')
            tracks.append((lba, sec_sz, os.path.join(base_dir, fname)))
    tracks.sort(key=lambda x: x[0], reverse=True)
    handles = [(lba, sec_sz, open(fp, "rb")) for lba, sec_sz, fp in tracks]

    def read_sec(lba):
        for start_lba, sec_sz, fh in handles:
            if lba >= start_lba:
                hdr = 16 if sec_sz == 2352 else 0
                fh.seek((lba - start_lba) * sec_sz + hdr)
                return fh.read(2048)
        return b"\x00" * 2048

    try:
        pvd = read_sec(45016)
        root_lba = int.from_bytes(pvd[158:162], "little")
        root_size = int.from_bytes(pvd[166:170], "little")
        buf = b"".join(read_sec(root_lba + i) for i in range((root_size + 2047) // 2048))
        items, pos = [], 0
        while pos < root_size:
            rl = buf[pos]
            if rl == 0:
                pos = ((pos // 2048) + 1) * 2048
                continue
            flba = int.from_bytes(buf[pos + 2 : pos + 6], "little")
            fsz = int.from_bytes(buf[pos + 10 : pos + 14], "little")
            flags = buf[pos + 25]
            nl = buf[pos + 32]
            nm = clean_iso_name(buf[pos + 33 : pos + 33 + nl].decode("ascii", "ignore"))
            if nm and nm.upper().endswith(".GDE") and not (flags & 2):
                items.append((nm, flba, fsz))
            pos += rl
        total = len(items)
        for idx, (nm, flba, fsz) in enumerate(items, 1):
            with open(os.path.join(out_dir, nm), "wb") as wf:
                rem, s = fsz, flba
                while rem > 0:
                    ch = read_sec(s)[: min(2048, rem)]
                    wf.write(ch)
                    rem -= len(ch)
                    s += 1
            if on_progress:
                on_progress(idx, total, nm)
        return total
    finally:
        for _, _, fh in handles:
            fh.close()

def extract_from_disc(disc_path, out_dir, on_progress=None):
    os.makedirs(out_dir, exist_ok=True)
    for old_f in os.listdir(out_dir):
        if old_f.upper().startswith("MUSIC_") or old_f.upper() == "SOUND":
            p = os.path.join(out_dir, old_f)
            if os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)
            else: os.remove(p)

    low = disc_path.lower()
    if low.endswith(".cdi"):
        count = extract_cdi_native(disc_path, out_dir, on_progress)
    elif low.endswith(".gdi"):
        count = extract_gdi_native(disc_path, out_dir, on_progress)
    elif low.endswith(".chd"):
        chdman = shutil.which("chdman") or os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "tools", "chdman.exe")
        if not os.path.exists(chdman):
            raise RuntimeError("Не найден chdman.exe для CHD")
        tmp = tempfile.mkdtemp(prefix="ecco_chd_")
        try:
            gdi_tmp = os.path.join(tmp, "disc.gdi")
            subprocess.run([chdman, "extractcd", "-i", disc_path, "-o", gdi_tmp], check=True, creationflags=0x08000000)
            count = extract_gdi_native(gdi_tmp, out_dir, on_progress)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        raise RuntimeError("Выберите .cdi, .chd или .gdi")

    cfg = os.path.join(os.path.dirname(os.path.dirname(out_dir)), "settings.ini")
    if not os.path.exists(cfg):
        with open(cfg, "w", encoding="utf-8") as sf:
            sf.write("mods = rus_paradox\n")
    return count

if __name__ == "__main__":
    _, src, dst = sys.argv
    extract_from_disc(src, dst)
