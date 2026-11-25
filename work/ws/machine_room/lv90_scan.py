"""lv90_scan.py - (19/11/2026) solo lettura. Regola `lv90dtp` del fork di Lukas (logica riscritta): il DTP nominato a
[Level+0x90]+0x1c (Level+0x90 = rilocazione esterna verso la sezione T, T+0x1c = idref tipo 7; famiglia {u32 n, ptr, ptr,
record float}) e' tutto s32 nei livelli base. Per ogni unit DLC della baseline confronta Xbox / PC parola per parola fuori
dagli slot di rilocazione e conta s32 / raw / s16 / altro; stampa le parole non s32.
uso: python -I -B lv90_scan.py BASELINE"""
import sys, os, struct, collections
R_ = '/path/to/trudlcport/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
BL = sys.argv[1]; SRC = R_ + 'work/baseline/%s/mods/' % BL
A = [Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')]
def xbox(rel):
    h = fcrc('xenon-w' + chr(92) + rel.replace('/', chr(92)))
    for ar in A:
        rs = [r for r in ar.idx if r['hash'] == h]
        if rs: return ar.read(rs[0])
def lv90(D, e):
    if not D.sections or D.sections[0].type != 0: return None
    t = {so: (si, do) for si, so, do in R.parse(bytes(D.sections[0].reloc), e).external}.get(0x90)
    if t is None or t[0] >= len(D.sections): return None
    si, do = t; T = D.sections[si]; r = R.parse(bytes(T.reloc), e)
    if {o: ty for ty, o in list(r.idref) + list(r.idref_a)}.get(do + 0x1c) != 7 or do + 0x20 > len(T.data): return None
    did = struct.unpack_from(('>' if e == 'be' else '<') + 'I', bytes(T.data), do + 0x1c)[0]
    return next((s for s in D.sections if s.type == 7 and s.id == did), None)
def slots(s, e):
    r = R.parse(bytes(s.reloc), e)
    return {o for o, _ in r.internal} | {so for _, so, _ in r.external} | {o for _, o in list(r.idref) + list(r.idref_a)}
def cls(x, p):
    if x == p: return 'raw' if x != x[::-1] else 'pal'
    if p == x[::-1]: return 's32'
    if p == x[1::-1] + x[:1:-1]: return 's16'
    return 'altro'
tot = collections.Counter()
for dp, dn, fn in os.walk(SRC):
    for f in sorted(fn):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(dp, f), SRC).replace(os.sep, '/')
        pr = open(os.path.join(dp, f), 'rb').read(); P = DW.read(pr, 'le'); ps = lv90(P, 'le')
        if ps is None: continue
        xr = xbox(rel)
        if xr is None: print(rel, 'nessun sorgente Xbox'); continue
        X = DW.read(xr, 'be'); xs = lv90(X, 'be')
        if xs is None or len(xs.data) != len(ps.data):
            print(rel, 'DTP PC', ps.id, len(ps.data), 'Xbox', None if xs is None else (xs.id, len(xs.data))); continue
        sl = slots(ps, 'le') | slots(xs, 'be'); c = collections.Counter(); bad = []
        for o in range(0, len(ps.data) - 3, 4):
            if o in sl: continue
            k = cls(xs.data[o:o + 4], ps.data[o:o + 4]); c[k] += 1
            if k not in ('s32', 'pal'): bad.append((o, xs.data[o:o + 4].hex(), ps.data[o:o + 4].hex(), k))
        tot.update(c)
        print('%-40s DTP %d (Xbox %d) %d B %s' % (rel, ps.id, xs.id, len(ps.data), dict(c)))
        for o, x, p, k in bad:
            fx = struct.unpack('>f', bytes.fromhex(x))[0]
            print('    +%#06x xbox %s pc %s %-5s float_xbox %g' % (o, x, p, k, fx))
print('totale', dict(tot))
