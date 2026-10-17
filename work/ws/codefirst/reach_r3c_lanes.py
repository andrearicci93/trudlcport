"""Raggiungibilita' strutturale (AST) delle lane PC decise da R3c / costanti solo-PC: arrivano alle uscite del blocco luci PC?"""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_struct import *
import mp_resolve
L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
CASES = {(981, 1531): [(112, 1), (113, 2)], (111, 225): [(107, 1)], (300, 356): [(107, 3), (109, 1)], (164, 207): [(106, 2), (106, 3)], (1409, 1038): [(108, 3), (110, 0)]}
for (xs, pd), lanes in CASES.items():
    res, ties = mp_resolve.resolve(xs, pd)
    C, _r, _t, out, _x, _p = struct_scores(xs, pd)
    CP2, CX2 = out[(1, 2)]; CP1, CX1 = out[(1, 1)]
    for l in lanes:
        reach = (l in CP2) or (l in CP1)
        print('(%d,%d) PC %s: regola %s | raggiunge le uscite del blocco PC (AST): %s' % (xs, pd, L(l), res.get(l), reach), flush=True)
