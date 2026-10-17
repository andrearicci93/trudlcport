import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_vn import *
C, res, ties = get_ctx(981, 1531)
XP, PP = C['XP'], C['PP']
rx = {100 + j: XP[j] for j in range(len(XP))}; rp = {100 + j: PP[j] for j in range(len(PP))}
px, tx = trace(C, 'x', rx, None); pp, tp = trace(C, 'p', rp, ALLB)
nx, npc = nodes(px, tx), nodes(pp, tp)
print(len(tx), len(tp), len(nx), len(npc))
h = align(nx, npc); print('allineati (valori reali)', len(h))
# miglior match per nodo PC con tolleranza larga
import numpy as np
cnt = 0
for n, c, it, v in npc[:40]:
    best = min(((np.abs(v - vx).mean(), m, cx) for m, cx, itx, vx in nx), default=(9, 0, 0))
    print(n, c, '%.4f' % best[0], best[1:])
