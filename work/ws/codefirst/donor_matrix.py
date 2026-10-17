"""Matrice donatore x xb: per ogni coppia base (xs,pd) della classe (blocco luci Xbox equivalente) usata come DONATORE con la regola di famiglia
(mp_resolve) e per ogni xb della classe, T(xb ; donatore) vs PC vero pb (luci on/off/mix, tutti i materiali ponte). Cella = min(on,off,mix) o FAIL.
Uso: donor_matrix.py XS  (classe di XS)"""
import sys, pickle, os
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *

xs0 = int(sys.argv[1])
cls = find_donors('X', xs0, 0, want=60)
L = libs(); x2 = x2p()
cls = [(a, b) for a, b in cls]
if not any(a == xs0 for a, _ in cls): cls = [(xs0, x2[xs0])] + cls
print('classe di %d:' % xs0, cls, flush=True)
rows = {}
for (ds, dp) in cls:
    try: res, ties = mp_resolve.resolve(ds, dp)
    except Exception as e: print('donatore', (ds, dp), 'resolve ERR', repr(e)[:100], flush=True); continue
    sc = {}
    for (xb, pb) in cls:
        try:
            o, info, n = one_pair(xb, pb, ds, dp, res)
            sc[(xb, pb)] = min(o.values())
        except Exception as e: sc[(xb, pb)] = -1.0
    rows[(ds, dp)] = (sc, dict(ties=len(ties), nres=len(res)))
    print('donatore', (ds, dp), 'pareggi', len(ties), 'PASS %d/%d' % (sum(v >= 0.99 for v in sc.values()), len(sc)), 'fallisce:', {k: round(v, 2) for k, v in sc.items() if v < 0.99}, flush=True)
pickle.dump(rows, open('donor_matrix_%d.pkl' % xs0, 'wb'))
