# Dettaglio per lingua dei conflitti reali (x in base e DLC-new): base, DLC1 pack10, TU/DLC2, id PC e testo PC oggi. Sola lettura.
import sys, pickle
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
V = {src: {s: (T[src][s]['lang'], T[src][s]['strings']) for s in T[src]} for src in T}
L.files_cache['pcpatch'] = {s: T['pcpatch'][s]['raw'] for s in T['pcpatch']}
m, info = L.build_map(V)
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
for x in [135, 410, 411, 412, 454, 460, 1289]:
    print('== x', x, 'pc id', m.get(x))
    for s in SPECS:
        X, U, P = V['xbase'][s][1], V['tu'][s][1], V['pack10'][s][1]
        PCs = V['pcpatch'][s][1]; p = m.get(x)
        pm = x >= len(P) or T['pack10'][s]['offs'][x] == 0
        d10 = 'MISS' if pm else P[x].decode('utf8', 'replace')[:50]
        print('  %s base=%r\n      dlc1=%r\n      tu =%r\n      pc_now=%r' % (LN[s], X[x].decode('utf8','replace')[:50] if x < len(X) else None, d10, U[x].decode('utf8','replace')[:50], PCs[p].decode('utf8','replace')[:50] if p is not None and p < len(PCs) else None))
