"""La lane PC decisa da R3c ha un effetto osservabile? Perturba la lane nel PC vero (donatore pd) e confronta l'output (luci on/off)."""
import sys, copy; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *
for xs, pd, lane in [(981, 1531, (100, 0)), (981, 1531, (103, 0)), (981, 1531, (112, 0)), (981, 1531, (112, 1)), (981, 1531, (114, 1))]:
    L = libs(); P = L['P']; blob = P[pd]['entries'][P[pd]['slots'][0]]['blob']; prog = decode_pc(blob)
    mats = material_pairs(xs, pd)
    for lab, bl in (('on', ALLB), ('off', {}), ('mix', {0: True, 3: True, 6: True})):
        sc = []
        for m in mats[:3]:
            PP = copy.deepcopy(m[3]); PP2 = copy.deepcopy(PP)
            r, c = lane[0] - 100, lane[1]
            try: PP2[r][c] = PP[r][c] + 0.37
            except TypeError: PP2 = [list(x) for x in PP]; PP2[r][c] = PP2[r][c] + 0.37
            sc.append(compare2(prog, prog, PP, PP2, bools=bl))
        print('(%d,%d) lane c%d.%s %s: uguaglianza output con lane+0.37 = %s' % (xs, pd, lane[0], 'xyzw'[lane[1]], lab, ['%.3f' % x for x in sc]), flush=True)
