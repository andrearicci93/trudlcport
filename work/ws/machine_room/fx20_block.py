"""fx20_block.py - (19/11/2026) solo lettura. DTP FX (testa: +0xc u16 n, +0x10 -> T, T+n*0x17c = fine) con puntatore interno a
+0x20 -> blocco B. Nel base (work/generic/store.pkl) conta per ogni offset di B (0..0x40) la classe PC della parola Xbox
(s32/raw/s16/altro; 'pal' escluso). Poi confronta con le stesse parole nei DTP FX della baseline (argomento) e stampa le
parole la cui classe non e' mai (o quasi) quella del base. uso: python -I -B fx20_block.py BASELINE"""
import sys, pickle, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/work/ws/b260_cannon'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
from fxcal_hdr import fxhdr
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb')); im = C.idmap().get(7, {})
def cls(x, p):
    if x == p: return 'pal' if x == x[::-1] else 'raw'
    if p == x[::-1]: return 's32'
    if p == x[1::-1] + x[:1:-1]: return 's16'
    return 'altro'
N = 0x40; base = collections.defaultdict(collections.Counter); nb = 0
for (t, xid), xs in S['xb_store'].items():
    if t != 7: continue
    p = S['pc_store'].get((7, im.get(xid, xid)))
    if not p or len(p['data']) != len(xs['data']): continue
    if not fxhdr(xs['data'], xs['reloc'], 'be'): continue
    B = dict(R.parse(xs['reloc'], 'be').internal).get(0x20)
    if B is None or B + N > len(xs['data']): continue
    nb += 1
    for k in range(0, N, 4):
        c = cls(xs['data'][B + k:B + k + 4], p['data'][B + k:B + k + 4])
        if c != 'pal': base[k][c] += 1
print('DTP FX base con blocco +0x20:', nb)
for k in range(0, N, 4): print('  B+%#04x %s' % (k, dict(base[k])))
print('--- baseline', sys.argv[1])
for rel, path in C.files(sys.argv[1]):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be'); Pd = DW.read(open(path, 'rb').read(), 'le'); pc = collections.defaultdict(list)
    for s in Pd.sections:
        if s.type == 7: pc[s.id].append(s)
    for x in X.sections:
        if x.type != 7 or not fxhdr(bytes(x.data), bytes(x.reloc), 'be'): continue
        ps = [p for p in pc.get(im.get(x.id, x.id), []) if len(p.data) == len(x.data)]
        B = dict(R.parse(bytes(x.reloc), 'be').internal).get(0x20)
        if len(ps) != 1 or B is None or B + N > len(x.data): continue
        bad = []
        for k in range(0, N, 4):
            c = cls(bytes(x.data[B + k:B + k + 4]), bytes(ps[0].data[B + k:B + k + 4])); tot = sum(base[k].values())
            if c != 'pal' and tot and base[k][c] * 20 < tot: bad.append('B+%#04x %s->%s %s (base %s)' % (k, x.data[B + k:B + k + 4].hex(), ps[0].data[B + k:B + k + 4].hex(), c, base[k].most_common(1)[0][0]))
        if bad: print('%-44s DTP %d B=+%#x: %s' % (rel, ps[0].id, B, '; '.join(bad)))
