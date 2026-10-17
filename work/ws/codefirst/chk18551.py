import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
from mp_cands import *
import mp_resolve
M = members(164, 207, 0)
for s in M:
    pm = s['pmap']; l = (106, 2)
    srcs = [k for k, v in (pm or {l: l}).items() if v == l]
    v = val(s['PP'], srcs[0]) if srcs else None
    if v is not None and abs(v - 1.0) > 1e-6: print('membro', s['tag'], 'c106.z =', v, 'srcs', srcs)
from task3_validate import *
for m in material_pairs(281, 337):
    if m[0] == 18551 or m[1] == 18551: print('materiale_pairs(281,337):', m[0], m[1], 'PP c106 =', list(m[3][6]), 'PP c105 =', list(m[3][5]))
