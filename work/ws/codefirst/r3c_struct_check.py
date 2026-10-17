"""Le 3 lane R3c NON innocue (21087, 23568, 21126): la firma strutturale/raggiungibilita' concorda con la scelta R3c (accordo esatto 17/19)?"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_struct import *
import mp_resolve
L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
for (xs, pd), lanes in {(111, 225): [(107, 1)], (300, 356): [(107, 3), (109, 1)], (981, 1531): [(112, 1), (113, 2)]}.items():
    res, ties = mp_resolve.resolve(xs, pd); AG = mp_resolve.AGR[(xs, pd, 0)]
    C, _r, _t, out, _x, _p = struct_scores(xs, pd); CP2, CX2 = out[(1, 2)]; CP1, CX1 = out[(1, 1)]
    for l in lanes:
        cands = list(AG[l]); live = [x for x in cands if x in CX2 or x in CX1]
        b, sc = best(out, l, cands)
        print('(%d,%d) PC %s: scelta R3c %s | candidati vivi %s | struttura: %s punteggi %s' % (xs, pd, L(l), res.get(l), [L(x) for x in live], b, {L(x): round(v, 2) for x, v in (sc or {}).items()}))
