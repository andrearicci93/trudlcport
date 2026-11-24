"""typelist_fix_gog.py - apply upstream trudlcport B272 + B273 (typelist_fix.py / typelist_fix2.py, commit ef2e1ff,
MIT, andrearicci93/trudlcport) to OUR doppelganger DRMs: the u8 markup-type lists in doppelganger DTP 20212 that were
converted as 32/16-bit words get their Xbox bytes back (rock vein type 22 readable again; F14).
Same offset table and the same safety checks as upstream: old bytes must match, only the expected words change,
round-trip of the DRM. Reads the given source files, writes new files to --out; never touches the game folder.
  python -I work/ws/gog/tools/typelist_fix_gog.py --out OUTDIR SRC_casual.drm SRC_costume_a.drm
"""
import sys, os, hashlib
WS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(WS, 'tomb-raider-underworld-dlc-pc', 'tools'))
import drm_write as DW
OFF = {0x7efb0: ('080e0016', '0e081600'), 0x7f020: ('1011121300001614', '1011121314160000'), 0x7f060: ('00000016', '16000000'),
       0x7f5b0: ('00000016', '16000000'), 0x7f5e0: ('00000016', '16000000'), 0x7f740: ('00000002', '02000000'),
       0x7ff00: ('00000016', '16000000'), 0x800c0: ('00001609', '09160000'), 0x801e0: ('00000017', '17000000'),
       0x80ee0: ('15080016', '08151600')}   # last entry = B273 (typelist_fix2)
a = sys.argv; outd = a[a.index('--out') + 1]; srcs = [x for x in a[1:] if x.endswith('.drm')]
os.makedirs(outd, exist_ok=True)
for src in srcs:
    raw = open(src, 'rb').read(); D = DW.read(raw, 'le')
    hit = [s for s in D.sections if s.type == 7 and s.id == 20212]; assert len(hit) == 1, src
    b = bytearray(hit[0].data)
    for o, (old, new) in OFF.items():
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        assert bytes(b[o:o + len(old)]) == old, (src, hex(o), b[o:o + len(old)].hex())
        b[o:o + len(new)] = new
    hit[0].data = bytes(b); o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0 = DW.read(raw, 'le'); D2 = DW.read(o_, 'le'); ch = set()
    for x, y in zip(D0.sections, D2.sections):
        assert (x.type, x.id, x.reloc, len(x.data)) == (y.type, y.id, y.reloc, len(y.data))
        if x.data != y.data: ch |= {(x.id, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
    exp = {(20212, o + k) for o, (old, new) in OFF.items() for k in range(0, len(bytes.fromhex(old)), 4)
           if bytes.fromhex(old)[k:k + 4] != bytes.fromhex(new)[k:k + 4]}
    assert ch == exp, sorted(ch)
    dst = os.path.join(outd, os.path.basename(src)); open(dst, 'wb').write(o_)
    print(os.path.basename(src), len(ch), 'words changed, md5', hashlib.md5(o_).hexdigest())
