#!/usr/bin/env python3
"""Estrattore XEX2 (Xbox 360) -> immagine PE decifrata/decompressa.

Scope: default.xex / OPEN-THIS.xex con encryption=normal (AES-128-CBC) e
compression=basic (blocchi raw + zero). LZX (compression normal/delta) e i
file .xexp (patch delta) NON sono implementati: vengono segnalati.

Chiave AES retail (16 byte) letta dal binario locale Xenia
(~/Downloads/Xenia-SteveRepack/xenia_canary.exe, offset 6964936) se non
passata con --key. Decifratura via CLI `openssl enc` (nessun pacchetto Python).

Uso (sola lettura sull'input):
  python3 -I tools/xex_extract.py IN.xex OUTDIR [--key HEX32]
Produce OUTDIR/<nome>.pe e stampa header, sezioni, entry, base, import.
"""
import os
import re
import struct
import subprocess
import sys

XENIA_BIN = os.path.expanduser("~/Downloads/Xenia-SteveRepack/xenia_canary.exe")
RETAIL_KEY_OFFSET = 6964936  # 20 b1 85 a5 9d 28 fd c3 40 58 3f bb 08 96 bf 91
RETAIL_KEY_HEX = "20b185a59d28fdc340583fbb0896bf91"

OPT_FILE_FORMAT = 0x000003FF
OPT_ENTRY = 0x00010100
OPT_BASE = 0x00010201
OPT_IMPORT_LIBS = 0x000103FF
OPT_RESOURCE = 0x000002FF


def aes_cbc_decrypt(key_hex, data):
    """AES-128-CBC decrypt, IV=0, nessun padding. Usa openssl CLI."""
    if len(data) % 16:
        raise ValueError("lunghezza dati non multipla di 16")
    cmd = ["/opt/homebrew/bin/openssl", "enc", "-d", "-aes-128-cbc", "-nopad",
           "-K", key_hex, "-iv", "00" * 16]
    r = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return r.stdout


def read_xenia_key():
    with open(XENIA_BIN, "rb") as f:
        f.seek(RETAIL_KEY_OFFSET)
        k = f.read(16)
    return k.hex()


def parse_header(d):
    magic, flags, pe_off, _res, sec_off, nopt = struct.unpack_from(">4sIIIII", d, 0)
    if magic != b"XEX2":
        raise ValueError("magic non XEX2: %r" % magic)
    opts = {}
    for i in range(nopt):
        k, v = struct.unpack_from(">II", d, 0x18 + 8 * i)
        opts.setdefault(k, v)
    return {"flags": flags, "pe_off": pe_off, "sec_off": sec_off, "nopt": nopt, "opts": opts}


def opt_data(d, h, key):
    """Ritorna (valore, bytes) per opt header: data inline se (key&0xff)==0, altrimenti offset."""
    if key not in h["opts"]:
        return None
    v = h["opts"][key]
    if key & 0xFF == 0:
        return v, None
    return v, d


def parse_security(d, sec_off):
    header_size, image_size = struct.unpack_from(">II", d, sec_off)
    info_size, image_flags, load_addr = struct.unpack_from(">III", d, sec_off + 0x108)
    file_key = d[sec_off + 0x150: sec_off + 0x160]
    import_count = struct.unpack_from(">I", d, sec_off + 0x128)[0]
    return {
        "header_size": header_size, "image_size": image_size, "info_size": info_size,
        "image_flags": image_flags, "load_address": load_addr,
        "file_key": file_key, "import_count": import_count,
    }


def parse_file_format(d, off):
    size = struct.unpack_from(">I", d, off)[0]
    enc, comp = struct.unpack_from(">HH", d, off + 4)
    blocks = []
    if comp == 1:  # basic: entries (data_size, zero_size)
        n = (size - 8) // 8
        for i in range(n):
            ds, zs = struct.unpack_from(">II", d, off + 8 + 8 * i)
            blocks.append((ds, zs))
            if ds == 0 and zs == 0:
                break
    return {"size": size, "enc": enc, "comp": comp, "blocks": blocks}


def decompress_basic(data_stream, blocks):
    out = bytearray()
    pos = 0
    for ds, zs in blocks:
        out += data_stream[pos:pos + ds]
        pos += ds
        out += b"\x00" * zs
    return bytes(out), pos


def parse_pe(img):
    if img[:2] != b"MZ":
        raise ValueError("PE: manca MZ")
    e_lfanew = struct.unpack_from("<I", img, 0x3C)[0]
    if img[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise ValueError("PE: manca signature")
    machine, nsec, _ts, _ps, _pn, opt_size, chars = struct.unpack_from("<HHIIIHH", img, e_lfanew + 4)
    opt = e_lfanew + 24
    magic = struct.unpack_from("<H", img, opt)[0]
    if magic == 0x10B:
        entry, base = struct.unpack_from("<II", img, opt + 16)
        image_base = struct.unpack_from("<I", img, opt + 28)[0]
        dd = opt + 96
    else:
        entry = struct.unpack_from("<I", img, opt + 16)[0]
        image_base = struct.unpack_from("<Q", img, opt + 24)[0]
        dd = opt + 112
    imp_rva, imp_size = struct.unpack_from("<II", img, dd + 8)
    sections = []
    so = opt + opt_size
    for i in range(nsec):
        name, vsize, va, rsize, rptr = struct.unpack_from("<8sIIII", img, so + 40 * i)[0:1] + struct.unpack_from("<IIII", img, so + 40 * i + 8)
        name_s = name.rstrip(b"\0").decode("ascii", "replace")
        sections.append({"name": name_s, "vsize": vsize, "va": va, "rsize": rsize, "rptr": rptr})
    return {"entry_rva": entry, "image_base": image_base, "sections": sections,
            "import_rva": imp_rva, "import_size": imp_size}


def file_off_to_va(pe, off):
    """Immagine in layout di memoria: offset file = VA - base (verificato su .text/.data)."""
    va = pe["image_base"] + off
    for s in pe["sections"]:
        if s["va"] <= off < s["va"] + max(s["vsize"], s["rsize"]):
            return va, s["name"]
    return va, None


def xbox_version(v):
    return "%d.%d.%d.%d" % ((v >> 28) & 0xF, (v >> 24) & 0xF, (v >> 8) & 0xFFFF, v & 0xFF)


def parse_exec_info(d, h):
    v = h["opts"].get(0x00040006)
    if v is None:
        return None
    media, ver, base_ver, title = struct.unpack_from(">IIII", d, v)
    platform, etype, disc, dcount = struct.unpack_from(">BBBB", d, v + 16)
    return {"media_id": media, "version": xbox_version(ver), "base_version": xbox_version(base_ver),
            "title_id": "%08X" % title, "platform": platform, "exec_type": etype,
            "disc": disc, "disc_count": dcount}


def parse_resources(d, h):
    v = h["opts"].get(OPT_RESOURCE)
    if v is None:
        return []
    size = struct.unpack_from(">I", d, v)[0]
    out = []
    p = v + 4
    while p + 16 <= v + size:
        name = d[p:p + 8].rstrip(b"\0").decode("ascii", "replace")
        addr, rsize = struct.unpack_from(">II", d, p + 8)
        out.append({"name": name, "addr": addr, "size": rsize})
        p += 16
    return out


def parse_import_libs(d, h):
    v = h["opts"].get(OPT_IMPORT_LIBS)
    if v is None:
        return []
    size, str_size, count = struct.unpack_from(">III", d, v)
    strings = d[v + 12: v + 12 + str_size]
    names = [x for x in strings.split(b"\0") if x]  # name_index = indice nella lista di stringhe non vuote
    libs = []
    p = v + 12 + str_size
    end = v + size
    while p + 4 <= end:
        rec_size = struct.unpack_from(">I", d, p)[0]
        if rec_size == 0:
            break
        name_index = struct.unpack_from(">H", d, p + 0x20 + 4)[0]
        nfuncs = struct.unpack_from(">H", d, p + 0x20 + 6)[0]
        name = names[name_index].decode("ascii", "replace") if name_index < len(names) else "?"
        libs.append({"name": name, "imports": nfuncs, "rec_size": rec_size})
        p += rec_size
    return libs


def find_strings(img, pe, needles):
    results = []
    for n in needles:
        for enc_name, pat in (("ascii", n.encode("ascii")), ("utf16le", n.encode("utf-16le"))):
            for m in re.finditer(re.escape(pat), img):
                off = m.start()
                va, sec = file_off_to_va(pe, off)
                results.append((n, enc_name, off, va, sec))
    return results


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, outdir = argv[1], argv[2]
    key = None
    if "--key" in argv:
        key = argv[argv.index("--key") + 1].lower()
    os.makedirs(outdir, exist_ok=True)

    with open(src, "rb") as f:
        d = f.read()
    h = parse_header(d)
    sec = parse_security(d, h["sec_off"])
    ff = parse_file_format(d, h["opts"][OPT_FILE_FORMAT]) if OPT_FILE_FORMAT in h["opts"] else None
    print("== header %s ==" % os.path.basename(src))
    print("module_flags=0x%08x pe_data_offset=0x%x security_off=0x%x opt_headers=%d size=%d"
          % (h["flags"], h["pe_off"], h["sec_off"], h["nopt"], len(d)))
    print("security: header_size=0x%x image_size=0x%x load_address=0x%08x import_count=%d"
          % (sec["header_size"], sec["image_size"], sec["load_address"], sec["import_count"]))
    if OPT_BASE in h["opts"]:
        print("base (opt 0x10201)=0x%08x" % h["opts"][OPT_BASE])
    if OPT_ENTRY in h["opts"]:
        print("entry (opt 0x10100)=0x%08x" % h["opts"][OPT_ENTRY])
    ei = parse_exec_info(d, h)
    if ei:
        print("exec info: title_id=%s version=%s base_version=%s media_id=0x%08x platform=%d exec_type=%d disc=%d/%d"
              % (ei["title_id"], ei["version"], ei["base_version"], ei["media_id"], ei["platform"],
                 ei["exec_type"], ei["disc"], ei["disc_count"]))
    for r in parse_resources(d, h):
        print("resource: name=%s addr=0x%08x size=0x%x" % (r["name"], r["addr"], r["size"]))
    if ff is None:
        print("file format info mancante")
        return 1
    print("file_format: enc=%d (1=normal AES) comp=%d (1=basic) blocks=%d"
          % (ff["enc"], ff["comp"], len(ff["blocks"])))
    if ff["comp"] != 1:
        print("NON SUPPORTATO: compression=%d (serve LZX)" % ff["comp"])
        return 3
    if ff["enc"] not in (0, 1):
        print("NON SUPPORTATO: encryption=%d" % ff["enc"])
        return 3

    if ff["enc"] == 1:
        if key is None:
            key = read_xenia_key()
            print("retail key: letta da xenia_canary.exe offset %d (%s)" % (RETAIL_KEY_OFFSET, key))
        session = aes_cbc_decrypt(key, sec["file_key"]).hex()
        print("session key (decifrata da file_key): %s" % session)
        data_in = d[h["pe_off"]:]
        data = aes_cbc_decrypt(session, data_in[: sum(b[0] for b in ff["blocks"])])
    else:
        session = None
        data = d[h["pe_off"]:]

    img, consumed = decompress_basic(data, ff["blocks"])
    print("decompress basic: consumed=%d bytes, image=%d bytes (security image_size=%d)"
          % (consumed, len(img), sec["image_size"]))
    out_pe = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pe")
    with open(out_pe, "wb") as f:
        f.write(img)
    print("scritto: %s" % out_pe)

    pe = parse_pe(img)
    print("== PE (layout memoria: offset file = VA - base) ==")
    entry_va = pe["image_base"] + pe["entry_rva"]
    print("image_base=0x%08x entry_rva=0x%08x entry_va=0x%08x (opt 0x10100=0x%08x)" % (
        pe["image_base"], pe["entry_rva"], entry_va, h["opts"].get(OPT_ENTRY, 0)))
    print("%-9s %-10s %-10s %-10s %-10s" % ("sect", "VA", "endVA", "VSize", "fileoff"))
    for s in pe["sections"]:
        print("%-9s 0x%08x 0x%08x 0x%08x 0x%06x" % (
            s["name"], pe["image_base"] + s["va"], pe["image_base"] + s["va"] + s["vsize"],
            s["vsize"], s["va"]))
    print("(PE raw pointers della tabella sezioni NON valgono per l'immagine: ignorati)")
    print("PE data dir[1] import: rva=0x%x size=0x%x (rva punta dentro la risorsa XDBF, probabilmente stale)"
          % (pe["import_rva"], pe["import_size"]))
    libs = parse_import_libs(d, h)
    print("== XEX import libraries (%d) ==" % len(libs))
    for L in libs:
        print("  %s  (%d funcs)" % (L["name"], L["imports"]))

    print("== stringhe StreamGroups / .drm ==")
    for n, enc_name, off, va, secn in find_strings(img, pe, ["StreamGroups", ".drm", "%sStreamGroups\\%s.drm"]):
        vs = "0x%08x" % va if va is not None else "fuori sezioni"
        print("  %-24s %-8s file=0x%06x VA=%s sez=%s" % (n, enc_name, off, vs, secn))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
