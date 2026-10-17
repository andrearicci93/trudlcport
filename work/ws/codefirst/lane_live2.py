"""Prova di liveness piu' forte (Giro 3): lane PC decise da R3c / costanti solo-PC. Perturbazioni multiple (+0.37,-0.3,+1.5,+10,=0,=1,=-1), 12 combinazioni di bool
(tutti on, tutti off, 10 casuali), TUTTI i materiali ponte. Se una qualsiasi perturbazione cambia l'output la lane e' VIVA (e la scelta R3c/costante non e' innocua)."""
import sys, copy, random; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *
CASES = [((981, 1531), [(100, 0), (112, 1), (113, 2)]), ((111, 225), [(107, 1)]), ((300, 356), [(107, 3), (109, 1)]), ((164, 207), [(106, 2), (106, 3)]), ((1409, 1038), [(108, 3), (110, 0)])]
MODS = [('+0.37', lambda v: v + 0.37), ('-0.3', lambda v: v - 0.3), ('+1.5', lambda v: v + 1.5), ('+10', lambda v: v + 10.0), ('=0', lambda v: 0.0), ('=1', lambda v: 1.0), ('=-1', lambda v: -1.0)]
rnd = random.Random(7)
keys = sorted(ALLB)
combos = [('on', dict(ALLB)), ('off', {})] + [('r%d' % i, {k: True for k in keys if rnd.random() < 0.5}) for i in range(10)]
L = libs(); P = L['P']
for (xs, pd), lanes in CASES:
    blob = P[pd]['entries'][P[pd]['slots'][0]]['blob']; prog = decode_pc(blob); mats = material_pairs(xs, pd)
    for lane in lanes:
        worst = (1.0, None); changed = 0; tot = 0
        for m in mats:
            PP = [list(x) for x in m[3]]; r, c = lane[0] - 100, lane[1]
            for mn, f in MODS:
                PP2 = [list(x) for x in PP]; PP2[r][c] = f(PP[r][c])
                if PP2[r][c] == PP[r][c]: continue
                for cn, bl in combos:
                    sc = compare2(prog, prog, PP, PP2, bools=bl); tot += 1
                    if sc < 0.999: changed += 1
                    if sc < worst[0]: worst = (sc, (m[0], mn, cn))
        print('(%d,%d) lane c%d.%s: %d prove, %d cambiano l\'output; uguaglianza minima %.3f %s -> %s' % (xs, pd, lane[0], 'xyzw'[lane[1]], tot, changed, worst[0], worst[1], 'VIVA' if changed else 'morta in tutte le prove'), flush=True)
