#!/usr/bin/env python3
import os, sys, struct, fnmatch

PATTERNS = ("*.GDE", "*.GSG", "*.INP", "0GDTEX.PVR", "AUDIO64.DRV", "CONFIG.TXT", "MUSIC_*.AFS", "SOUND/*.KAT")

def match_name(rel_path):
    head, _, _ = rel_path.replace("\\", "/").lstrip("/").partition(";")
    return head if any(fnmatch.fnmatch(head.upper(), p) for p in PATTERNS) else None

def extract_cdi(disc_path, out_dir):
    with open(disc_path, "rb") as f:
        blob = f.read()
    pvd_pos = blob.rfind(b"\x01CD001\x01")
    data_pvd = blob.find(b"\x01CD001\x01", 1000000)
    if pvd_pos < 0:
        raise RuntimeError("ISO9660 PVD not found in CDI")
    if pvd_pos >= 24 and blob[pvd_pos - 24:pvd_pos - 12] == b"\x00" + b"\xff" * 10 + b"\x00":
        sec_size = 2352
    elif pvd_pos >= 8 and blob[pvd_pos - 8:pvd_pos] == b"\x00\x00\x08\x00\x00\x00\x08\x00":
        sec_size = 2336
    else:
        sec_size = 2336
    pvd = blob[pvd_pos:pvd_pos + 2048]
    root_lba, = struct.unpack_from("<I", pvd, 158)
    root_len, = struct.unpack_from("<I", pvd, 166)
    sess_lba = 0
    def read_extent(lba, size, is_dir=False):
        out = bytearray()
        rem = size
        cur = lba
        while rem > 0:
            pos = (pvd_pos if is_dir else data_pvd) + (cur - 16) * sec_size
            chunk = min(2048, rem)
            out.extend(blob[pos:pos + chunk])
            rem -= chunk
            cur += 1
        return bytes(out)
    count = 0
    def walk_dir(lba, length, prefix=""):
        nonlocal count
        buf = read_extent(lba, length, True)
        off = 0
        while off + 33 <= len(buf):
            rec_len = buf[off]
            if rec_len == 0:
                off = ((off // 2048) + 1) * 2048
                continue
            elba, = struct.unpack_from("<I", buf, off + 2)
            elen, = struct.unpack_from("<I", buf, off + 10)
            flags = buf[off + 25]
            nlen = buf[off + 32]
            raw_name = buf[off + 33:off + 33 + nlen].decode("latin1", errors="ignore")
            off += rec_len
            if raw_name in ("\x00", "\x01"):
                continue
            clean, _, _ = raw_name.partition(";")
            rel = f"{prefix}/{clean}" if prefix else clean
            if flags & 2:
                walk_dir(elba, elen, rel)
            else:
                matched = match_name(rel)
                if matched:
                    dst = os.path.join(out_dir, *matched.split("/"))
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(dst, "wb") as wf:
                        wf.write(read_extent(elba, elen))
                    count += 1
    walk_dir(root_lba, root_len)
    return count

def extract_from_disc(disc_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    if disc_path.lower().endswith(".cdi"):
        count = extract_cdi(disc_path, out_dir)
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
    if not os.path.exists(cfg):
        with open(cfg, "w", encoding="utf-8") as sf:
            sf.write("mods = rus_paradox\n")
    print(f"Extracted {count} Paradox RUS mod files into {out_dir}")

if __name__ == "__main__":
    _, src, dst = sys.argv
    extract_from_disc(src, dst)