"""link_ratio_fix.py - record UberObject di collegamento fra giunti {u8 0x0b, pad, ptr giunto A, ptr giunto B, f32 rapporto}:
il motore PC legge +0xc come FLOAT (FUN_004d7ed0: 0x4d7f31 'fld dword [edi+0xc]' -> FUN_004e17b0(A, B, rapporto)).
Base: 23/23 record di collegamento con +0xc convertito s32 (1.0 / 0.5 / 0.75). Il convertitore DLC lo lasciava RAW
(byte0-first come i selettori dei record giunto 0..4): dlc1_uo_sewer_gate DTP 20754 @712 c0000000 (-2.0 Xbox) -> 2.7e-43 PC,
giunti scollegati: la sbarra scende da sola fino alla finestra della condizione 0xe (azione 20) e il cancello resta chiuso.
Riconoscimento: byte0 == 0x0b, byte1..3 == 0, +4 e +8 puntatori interni a due record giunto distinti (byte0 in 0..4).
Usage (python -I): tools/venv/bin/python -I tools/link_ratio_fix.py selftest | scan [DIR] | fix OUTDIR [DIR]
Hook: fix_section(xd, xreloc, pd) -> (bytes, [(off, old, new)])   (dopo convert, solo sezioni type 7)"""
import sys, os, struct, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
JOINT_TYPES = (0, 1, 2, 3, 4)

def links(xd, rel):
    it = dict(rel.internal)
    for o in range(0, len(xd) - 0x10, 4):
        if xd[o] != 0x0b or xd[o + 1:o + 4] != b'\0\0\0': continue
        a, b = it.get(o + 4), it.get(o + 8)
        if a is None or b is None or a == b: continue
        if a + 4 > len(xd) or b + 4 > len(xd) or xd[a] not in JOINT_TYPES or xd[b] not in JOINT_TYPES: continue
        yield o

def fix_section(xd, xreloc, pd):
    rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    out = bytearray(pd); log = []
    for o in links(xd, rel):
        w = o + 0xc
        if w in skip: continue
        new = xd[w:w + 4][::-1]
        if bytes(out[w:w + 4]) != new:
            log.append((w, bytes(out[w:w + 4]).hex(), new.hex())); out[w:w + 4] = new
    return bytes(out), log

def selftest():
    import dtp_audit as A
    n = ch = k = 0
    for x, p, xb, pc, xr in A.base_pairs():
        nb, lg = fix_section(xb['data'], xr, pc['data']); n += 1; ch += len(lg)
        k += sum(1 for _ in links(xb['data'], R.parse(xr, 'be') if isinstance(xr, (bytes, bytearray)) else xr))
    print('base pairs', n, 'link records', k, 'words changed', ch)

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
    elif a[0] == 'scan': scan(a[1] if len(a) > 1 else os.path.join(W, 'baseline', 'B83', 'mods'))
    elif a[0] == 'fix': scan(a[2] if len(a) > 2 else os.path.join(W, 'baseline', 'B83', 'mods'), a[1])
