# Per gli id PC richiesti (e per ogni id PC toccato dal merge): preimmagine Xbox, testi base/DLC1/TU, e cosa fa oggi il merge. Sola lettura.
import sys, pickle, json, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
V = {src: {s: (T[src][s]['lang'], T[src][s]['strings']) for s in T[src]} for src in T}
L.files_cache['pcpatch'] = {s: T['pcpatch'][s]['raw'] for s in T['pcpatch']}
m, info = L.build_map(V)
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
inv = collections.defaultdict(list)
for x, p in m.items(): inv[p].append(x)
# 1) all x where TU differs from base (any lang) and what the merge does
touch = collections.defaultdict(set)   # pc id -> set of (x)
for s in SPECS:
    X, U, P = V['xbase'][s][1], V['tu'][s][1], V['pack10'][s][1]
    for x in range(1, len(U)):
        if x < len(X) and U[x] != X[x]:
            touch[m[x]].add(x)
print('x base changed by TU (any lang):', sorted({x for p in touch for x in touch[p]}))
print('pc ids the merge may touch via base changes:', len(touch), 'of which in requested set:', sorted(p for p in touch if p in set([1288,1289]+list(range(1291,1298))+list(range(1316,1376)))))
req = [1288, 1289] + list(range(1291, 1298)) + list(range(1316, 1376))
hit = [p for p in req if p in touch]
print('requested pc ids the merge changes:', hit)
# 2) for these, per-language detail
for p in hit:
    for x in sorted(touch[p]):
        for s in SPECS:
            X, U, P = V['xbase'][s][1], V['tu'][s][1], V['pack10'][s][1]
            PCs = V['pcpatch'][s][1]; PO = T['pcpatch'][s]['offs']
            pm = (x >= len(P)) or (T['pack10'][s]['offs'][x] == 0)
            print('pc %d x %d %s | base=%r | dlc1=%s | tu=%r | pc_now=%r | merge_changes=%s' % (
                p, x, LN[s], X[x][:40] if x < len(X) else None, 'MISSING' if pm else repr(P[x][:40]),
                U[x][:40], PCs[p][:40], (U[x] != X[x] and PCs[p] == X[x])))
