"""tag403_fix.py - record DTP {tag 0x403, 0, 0, u16 0x300 (BE 00030000)} (id univoco persistente di un oggetto; il motore PC lo legge
come u32 in 0x6b4b7a e lo testa nel bitset [[0xc59264]+0x3ed90] (4128 bit) con 0x5d60a0): la parola +0x30 e' u32 s32.
generic_type0.convert_section0 la lascia 'raw' (0x000000dd -> 0xdd000000) per i record il cui label di regione (1128) non ha voti per
la shape B3 -> AV 0x5d60bb (crash5d, dlc_dungeonhalla 20493@0x6660).  Base: 174/174 record con +0x30 s32.
Usage (python -I): tools/venv/bin/python -I tools/tag403_fix.py selftest | scan [DIR] | fix OUTDIR [DIR]
Hook: fix_section(xd, xreloc, pd) -> (bytes, [(off, old, new)])   (dopo convert, solo sezioni type 7)"""
import sys, os, struct, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
REC = (0x403, 0, 0, 0x30000)       # Xbox BE words +0..+0xc

def fix_section(xd, xreloc, pd):
    rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    out = bytearray(pd); log = []
    for o in range(0, len(xd) - 0x34, 4):
        if xd[o:o + 4] != b'\x00\x00\x04\x03' or struct.unpack_from('>IIII', xd, o) != REC: continue
        w = o + 0x30
        if w in skip: continue
        v = struct.unpack_from('>I', xd, w)[0]
        if v == 0 or v >= 0x1020: continue                       # id 1..4127 (bitset 0x204 byte)
        new = struct.pack('<I', v)
        if bytes(out[w:w + 4]) != new:
            log.append((w, bytes(out[w:w + 4]).hex(), new.hex())); out[w:w + 4] = new
    return bytes(out), log

def selftest():
    import dtp_audit as A
    n = ch = 0
    for x, p, xb, pc, xr in A.base_pairs():
        nb, lg = fix_section(xb['data'], xr, pc['data']); n += 1; ch += len(lg)
    print('base pairs', n, 'words changed', ch)

def scan(d, outdir=None):
    import dtp_audit as A, hashlib
    md5 = []; total = 0
    for p in sorted(glob.glob(d + '/**/*.drm', recursive=True)):
        rel = os.path.relpath(p, d).replace('\\', '/'); xs = A.xsecs(rel)
        if xs is None: continue
        raw = open(p, 'rb').read(); D = DW.read(raw, 'le'); dirty = False
        for x, i in A.section_pairs(xs, D):
            sec = D.sections[i]
            if x['type'] != 7 or len(sec.data) != len(x['data']): continue
            nb, lg = fix_section(x['data'], x['reloc'], sec.data)
            for w, a, b in lg: print(rel, sec.id, hex(w), a, '->', b); total += 1
            if lg: sec.data = nb; dirty = True
        if dirty and outdir:
            o = os.path.join(outdir, rel); os.makedirs(os.path.dirname(o), exist_ok=True)
            data = DW.cdrm_encode(D.write('le'), 'le') if raw[:4] == b'CDRM' else D.write('le')
            open(o, 'wb').write(data); md5.append('%s  %s' % (hashlib.md5(data).hexdigest(), rel))
    print('words', total)
    if outdir: open(os.path.join(outdir, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'selftest': selftest()
    elif a[0] == 'scan': scan(a[1] if len(a) > 1 else os.path.join(W, 'baseline', 'B5', 'mods'))
    elif a[0] == 'fix': scan(a[2] if len(a) > 2 else os.path.join(W, 'baseline', 'B5', 'mods'), a[1])
