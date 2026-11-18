import os, sys, shutil, tempfile, subprocess, struct, glob, fnmatch

PATTERNS = ("*.GDE", "*.GSG", "*.INP", "0GDTEX.PVR", "AUDIO64.DRV", "CONFIG.TXT", "MUSIC_*.AFS", "SOUND/*.KAT")

def match_name(rel_path):
    head, _, _ = rel_path.replace("\\", "/").lstrip("/").partition(";")
    return head if any(fnmatch.fnmatch(head.upper(), p) for p in PATTERNS) else None

def extract_iso_2048(iso_path, out_dir):
    with open(iso_path, "rb") as f:
        blob = f.read()
    pvd_off = blob.find(b"\x01CD001\x01")
    if pvd_off < 0:
        raise RuntimeError("PVD not found in ripped ISO")
    sec_sz = 2336 if (pvd_off % 2048 != 0 and (pvd_off - 8) % 2336 == 0) else 2048
    data_off = 8 if sec_sz == 2336 else 0
    pvd_idx = (pvd_off - data_off) // sec_sz
    base_lba = 11700 - (pvd_idx - 16)
    pvd = blob[pvd_off : pvd_off + 2048]
    root_lba, = struct.unpack_from("<I", pvd, 158)
    root_len, = struct.unpack_from("<I", pvd, 166)
    def read_sec(lba, size):
        out = bytearray()
        rem, cur = size, lba
        while rem > 0:
            off = (cur - base_lba) * sec_sz + data_off
            chunk = min(2048, rem)
            out.extend(blob[off : off + chunk])
            rem -= chunk
            cur += 1
        return bytes(out)
    count = 0
    def walk(lba, length, prefix=""):
        nonlocal count
        buf = read_sec(lba, length)
        off = 0
        while off + 33 <= len(buf):
            rl = buf[off]
            if rl == 0:
                off = ((off // 2048) + 1) * 2048
                continue
            elba, = struct.unpack_from("<I", buf, off + 2)
            elen, = struct.unpack_from("<I", buf, off + 10)
            flags = buf[off + 25]
            nl = buf[off + 32]
            raw = buf[off + 33 : off + 33 + nl].decode("latin1", errors="ignore")
            off += rl
            if raw in ("\x00", "\x01"):
                continue
            clean, _, _ = raw.partition(";")
            rel = f"{prefix}/{clean}" if prefix else clean
            if flags & 2:
                walk(elba, elen, rel)
            else:
                matched = match_name(rel)
                if matched:
                    dst = os.path.join(out_dir, *matched.split("/"))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(dst, "wb") as wf:
                        wf.write(read_sec(elba, elen))
                    count += 1
    walk(root_lba, root_len)
    return count

def extract_from_disc(disc_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    if disc_path.lower().endswith(".cdi"):
        cdirip = shutil.which("cdirip")
        if not cdirip:
            raise RuntimeError("cdirip.exe not found in PATH")
        tmp_dir = tempfile.mkdtemp(prefix="ecco_cdirip_")
        try:
            subprocess.run([cdirip, os.path.abspath(disc_path), tmp_dir, "-iso"], check=True)
            isos = sorted(glob.glob(os.path.join(tmp_dir, "tdata*.iso")))
            if not isos:
                raise RuntimeError("cdirip produced no data ISO tracks")
            count = extract_iso_2048(isos[-1], out_dir)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        from dcdisc.image import open_image
        count = 0
        with open_image(disc_path) as img:
            for rel_path, data in img.walk_files():
                matched = match_name(rel_path)
                if matched:
                    dst = os.path.join(out_dir, *matched.split("/"))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(dst, "wb") as f:
                        f.write(data)
                    count += 1
    cfg = os.path.join(os.path.dirname(os.path.dirname(out_dir)), "settings.ini")
    with open(cfg, "w", encoding="utf-8") as sf:
        sf.write("mods = rus_paradox\n")
    print(f"Extracted {count} Paradox RUS mod files into {out_dir}")

if __name__ == "__main__":
    _, src, dst = sys.argv
    extract_from_disc(src, dst)