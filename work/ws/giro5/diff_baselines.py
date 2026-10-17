"""Diff per sezione (type,id) di un DRM tra baseline: numero di byte diversi per sezione (data) e reloc diversi."""
import sys, os
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW
R = '/path/to/trudlcport/work/baseline/'
name, ref, others = sys.argv[1], sys.argv[2], sys.argv[3:]
def load(b):
    p = R + b + '/mods/' + name
    return {(s.type, s.id, i): s for i, s in enumerate(DW.read(DW.cdrm_decode(open(p, 'rb').read(), 'le') if open(p, 'rb').read(4) == b'CDRM' else open(p, 'rb').read(), 'le').sections)}
A = load(ref)
for o in others:
    Bm = load(o)
    ka = {(t, i) for t, i, _ in A}; kb = {(t, i) for t, i, _ in Bm}
    da = {(t, i): s for (t, i, _), s in A.items()}; db = {(t, i): s for (t, i, _), s in Bm.items()}
    ch = []
    for k in sorted(ka & kb):
        x, y = da[k], db[k]
        if x.data != y.data or x.reloc != y.reloc:
            n = 'len %d/%d' % (len(x.data), len(y.data)) if len(x.data) != len(y.data) else sum(1 for i in range(len(x.data)) if x.data[i] != y.data[i])
            ch.append((k, n, 'reloc diverso' if x.reloc != y.reloc else ''))
    print('%s: %s vs %s | solo %s: %d sez | solo %s: %d sez | cambiate: %d' % (name, ref, o, ref, len(ka - kb), o, len(kb - ka), len(ch)))
    types = {}
    for k, n, r in ch: types.setdefault(k[0], []).append((k[1], n))
    for t, v in sorted(types.items()): print('   tipo %d: %d sezioni, es. %s' % (t, len(v), v[:6]))
