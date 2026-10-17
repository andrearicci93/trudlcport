"""portal_fix.py - portal {u16 start, u16 count} words of cell sections (type 0) left as u32 by the learned type-0 table (crash 0x167f01, 2026-10-13).

Defect: in a SceneCell/OcclusionTree record array (0x40 B records, the sentinel 0xbeebbeeb at +0x04 of each record) the word at
(marker - 4) is {u16 start, u16 count}: portal vertices [start, start+count) in the cell pool.  Xbox BE 00 50 00 04 -> PC must be the
u16-pair swap (50 00 04 00).  generic_type0.convert_section0 picked u32 (s32) for 9 words of dlc_dungeon.drm (sec idx 47 x8, idx 51 x1)
-> 04 00 50 00: wrong ranges, count 0x5c -> stack overflow in the frustum clip fn 0x567d90.  Root cause: see work/ws/integ/REPORT.md (e).
Rule (HEURISTIC, from work/ws/crash167/pairfix.py): a 4-aligned marker 0xbeebbeeb that has another marker at +-0x40 (record array), and
the BE halves hi,lo both in 1..0x3ff  ->  the PC word is the u16-pair swap of the Xbox word.
Calibration: 806/806 portal records on the base pairs are u16-swapped; selftest = 0 words changed on every type-0 base pair section.
UNCERTAINTY: (i) the marker-neighbour criterion (+-0x40) and the 1..0x3ff bound are empirical (the 5 base words 'hi,lo nonzero' outside
the rule are floats/non-portal values); a portal with start or count >= 0x400, or an isolated record, is NOT touched; (ii) a word that is
a reloc slot is never written.
Usage (python -I): tools/venv/bin/python -I tools/portal_fix.py selftest | scan [DIR]
Hook: fix_section(xd, xreloc, pd) -> (bytes, [(off, old, new)])    (dlc_generic.convert_drm, extra_fixes, type 0 only; idempotent)"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
MK = b'\xbe\xeb\xbe\xeb'

def _swap(xw): return xw[1::-1] + xw[3:1:-1]

def candidates(xd):
    pos = []; m = xd.find(MK)
    while m >= 0:
        if m % 4 == 0 and m >= 4: pos.append(m)
        m = xd.find(MK, m + 1)
    S = set(pos)
    for m in pos:
        if (m + 0x40 in S) or (m - 0x40 in S):
            hi, lo = struct.unpack('>HH', xd[m - 4:m])
            if 0 < hi < 0x400 and 0 < lo < 0x400: yield m - 4

def fix_section(xd, xreloc, pd):
    """-> (new pd bytes, [(off, old_hex, new_hex)]).  xreloc: BE reloc (parsed or blob) or None."""
    if len(pd) != len(xd): return bytes(pd), []
    skip = set()
    if xreloc is not None:
        rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
        skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    b = bytearray(pd); log = []
    for o in candidates(xd):
        if o in skip: continue
        w = _swap(xd[o:o + 4])
        if bytes(b[o:o + 4]) != w: log.append((o, bytes(b[o:o + 4]).hex(), w.hex())); b[o:o + 4] = w
    return bytes(b), log

def selftest():
    import pickle, generic_ids as GI
    P = pickle.load(open(os.path.join(W, 'generic', 'pairs.pkl'), 'rb'))
    n = nc = nw = 0; fp = []
    for nm, ((xh, sx), (ph, sp)) in sorted(P.items()):
        try: ms = list(GI.section_matches(sx, sp, None))
        except Exception: continue
        for i, j, stg in ms:
            a, bb = sx[i], sp[j]
            if a['type'] != 0 or a['data'] is None or bb['data'] is None or len(a['data']) != len(bb['data']): continue
            n += 1; nw += sum(1 for _ in candidates(a['data']))
            _, ch = fix_section(a['data'], a['reloc'], bb['data']); nc += len(ch)
            fp += [(nm, i, hex(o), x, y) for o, x, y in ch]
    print('base type0 sections', n, 'portal words matched by the rule', nw, 'words changed', nc); print(fp[:10])
    return nc

def scan(d):
    import glob, drm_write as DW, dtp_audit as A
    tot = 0
    for p in sorted(glob.glob(d + '/**/*.drm', recursive=True)):
        rel = os.path.relpath(p, d).replace('\\', '/'); xs = A.xsecs(rel)
        if xs is None: continue
        D = DW.read(open(p, 'rb').read(), 'le')
        xz = [x for x in xs if x['type'] == 0 and x['data'] is not None]                    # type 0 has no ids: pair by order
        pz = [i for i, q in enumerate(D.sections) if q.type == 0]
        if len(xz) != len(pz): print(rel, 'type-0 count mismatch', len(xz), len(pz)); continue
        for x, i in zip(xz, pz):
            if len(D.sections[i].data) != len(x['data']): continue
            _, lg = fix_section(x['data'], x['reloc'], D.sections[i].data)
            for o, a, b in lg: print(rel, 'sec', i, hex(o), a, '->', b); tot += 1
    print('words', tot)

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'selftest': selftest()
    elif a[0] == 'scan': scan(a[1] if len(a) > 1 else os.path.join(W, 'baseline', 'B6', 'mods'))
