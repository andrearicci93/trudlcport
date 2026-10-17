import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from mp_cands import members, val
def exact(mp, lane):
    if mp is None: return lane
    k = [kk for kk, v in mp.items() if v == lane]; return k[0] if k else None
for (xs, pd), lanes in {(300, 356): [(107, 3), (109, 1)], (981, 1531): [(112, 1), (113, 2)], (111, 225): [(107, 1)]}.items():
    M = members(xs, pd, 0)
    for l in lanes:
        print((xs, pd), 'c%d.%s' % (l[0], 'xyzw'[l[1]]), [(s['tag'], round(float(val(s['PP'], exact(s['pmap'], l))), 3)) for s in M if exact(s['pmap'], l) is not None and val(s['PP'], exact(s['pmap'], l)) is not None and abs(val(s['PP'], exact(s['pmap'], l)) - (1.0 if l in ((107,3),(112,1),(107,1)) else 0.0)) > 1e-6])
