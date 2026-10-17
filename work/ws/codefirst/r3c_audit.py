"""Audit R3c: per ogni lane decisa da R3c, accordo ESATTO per coppia-di-lib (campioni raggruppati) fra lane PC e ciascun candidato."""
import sys, collections; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import mp_resolve, mp_cands
from mp_resolve import *
from mp_cands import members, val
def exact(mp, lane):
    if mp is None: return lane
    k = [kk for kk, v in mp.items() if v == lane]; return k[0] if k else None
for xs, pd in [(981, 1531), (111, 225), (300, 356)]:
    res, ties = mp_resolve.resolve(xs, pd)
    M = members(xs, pd)
    print('=== (%d,%d) campioni %d' % (xs, pd, len(M)))
    for l, sc in mp_resolve.AGR[(xs, pd, 0)].items():
        print(' lane PC c%d.%s -> %s  accordi %s' % (l[0], 'xyzw'[l[1]], res[l], {('c%d.%s' % (x[0], 'xyzw'[x[1]])): v for x, v in sc.items()}))
        for x in sc:
            by = collections.defaultdict(lambda: [0, 0])
            for s in M:
                a, b = exact(s['pmap'], l), exact(s['xmap'], x)
                if a is None or b is None: continue
                va, vb = val(s['PP'], a), val(s['XP'], b)
                if va is None or vb is None: continue
                g = by[(s['tag'][0], s['tag'][1], s['tag'][2])]; g[1] += 1; g[0] += abs(va - vb) < 1e-6
            bad = {k: tuple(v) for k, v in by.items() if v[0] != v[1]}
            print('    cand c%d.%s: coppie con disaccordo %s' % (x[0], 'xyzw'[x[1]], bad))
