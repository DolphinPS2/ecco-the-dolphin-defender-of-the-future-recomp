#!/usr/bin/env python3
import os, sys, struct, fnmatch

PATTERNS = ("*.GDE", "*.GSG", "*.INP", "0GDTEX.PVR", "AUDIO64.DRV", "CONFIG.TXT", "MUSIC_*.AFS", "SOUND/*.KAT")

def match_name(rel_path):
    head, _, _ = rel_path.replace("\\", "/").lstrip("/").partition(";")
    return head if any(fnmatch.fnmatch(head.upper(), p) for p in PATTERNS) else None

def parse_cdi_tracks(blob):
    # DiscJuggler v2/v3/v3.5 footer: last 8 bytes = (version, header_offset_from_end)
    ver, h_off = struct.unpack_from("<II", blob, len(blob) - 8)
    pos = len(blob) - h_off if ver == 0x80000006 else h_off
    sessions = struct.unpack_from("<H", blob, pos)[0]
    pos += 2
    tracks = []
    cur_byte = 0
    cur_lba = 0
    for _ in range(sessions):
        ntracks = struct.unpack_from("<H", blob, pos)[0]
        pos += 2
        for _ in range(ntracks):
            # Skip variable pre-track marker (00 00 01 00 00 00 FF FF FF FF repeated)
            while blob[pos:pos+4] == b"\x00\x00\x01\x00":
                pos += 10
            pos += 4 # unknown 4 bytes
            fn_len = blob[pos]
            pos += 1 + fn_len + 11 + 4 + 4
            pregap, length = struct.unpack_from("<II", blob, pos)
            pos += 14
            mode = struct.unpack_from("<I", blob, pos)[0]
            pos += 12
            start_lba = struct.unpack_from("<I", blob, pos)[0]
            total_len = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 29
            if ver != 0x80000004:
                pos += 5
                if struct.unpack_from("<I", blob, pos)[0] == 0xFFFFFFFF:
                    pos += 78
                pos += 4
            sec_size = 2048 if mode == 0 else (2336 if mode == 1 else 2352)
            data_off = 24 if sec_size == 2352 else (8 if sec_size == 2336 else 0)
            tracks.append((start_lba, total_len, cur_byte + pregap * sec_size, sec_size, data_off))
            cur_byte += total_len * sec_size
        pos += 12
    return tracks

def extract_cdi(disc_path, out_dir):
    with open(disc_path, "rb") as f:
        blob = f.read()
    pvd_pos = blob.rfind(b"\x01CD001\x01")
    if pvd_pos < 0:
        raise RuntimeError("ISO9660 PVD not found in CDI")
    sec_size = 2352 if (pvd_pos >= 24 and blob[pvd_pos - 24:pvd_pos - 12] == b"\x00" + b"\xff" * 10 + b"\x00") else 2336
    pvd = blob[pvd_pos:pvd_pos + 2048]
    root_lba, = struct.unpack_from("<I", pvd, 158)
    root_len, = struct.unpack_from("<I", pvd, 166)
    try:
        tracks = parse_cdi_tracks(blob)
    except Exception:
        tracks = []
    def lba_to_pos(cur, is_dir=False):
        if is_dir:
            return pvd_pos + (cur - 16) * sec_size
        for s_lba, t_len, base_b, s_sz, d_off in tracks:
            if s_lba <= cur < s_lba + t_len:
                return base_b + (cur - s_lba) * s_sz + d_off
        if cur >= 400000:
            return -278651896 + cur * sec_size
        if cur >= 259754:
            return -255107352 + cur * sec_size
        return 4800680 + cur * sec_size
    def read_extent(lba, size, is_dir=False):
        out = bytearray()
        rem = size
        cur = lba
        while rem > 0:
            pos = lba_to_pos(cur, is_dir)
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
    if not os.environ.get('DCDISC_LIBCHDR'):
        for c in (os.path.join(os.getcwd(), '.deps', 'libchdr-build', 'chdr.dll'), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine', 'chdr.dll')):
            if os.path.exists(c): os.environ['DCDISC_LIBCHDR'] = os.path.abspath(c); break
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
    with open(cfg, "w", encoding="utf-8") as sf:
        sf.write("mods = rus_paradox\n")
    print(f"Extracted {count} Paradox RUS mod files into {out_dir}")

if __name__ == "__main__":
    _, src, dst = sys.argv
    extract_from_disc(src, dst)