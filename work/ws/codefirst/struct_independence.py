"""Indipendenza delle decisioni strutturali: per ogni lane in pareggio, punteggio di contesto di OGNI candidato (senza 'used', senza filtro di raggiungibilita'), livelli (1,2) e (1,1)."""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_struct import *
import mp_resolve
xs, pd = 1431, 1060
res, ties = mp_resolve.resolve(xs, pd)
C, _r, _t, out, CXall, CPall = struct_scores(xs, pd)
L = lambda l: 'c%d.%s' % (l[0], 'xyzw'[l[1]])
CP2, CX2 = out[(1, 2)]
for l in sorted(ties):
    cands = [tuple(x) for x in ties[l]]
    live = [L(x) for x in cands if x in CX2]
    print('PC %s: candidati %s | vivi (raggiungono le uscite Xbox): %s' % (L(l), [L(x) for x in cands], live))
    for tier in ((1, 2), (1, 1)):
        b, sc = best({tier: out[tier]}, l, cands) if False else (None, None)
    b, sc = best(out, l, cands)
    print('    best(tutti i candidati, nessun filtro): %s' % (str(b)[:120],), '| punteggi', {L(x): round(v, 2) for x, v in (sc or {}).items()})
    b2, sc2 = best(out, l, [x for x in cands if x in CX2])
    print('    best(solo vivi)                        : %s' % (str(b2)[:120],), '| punteggi', {L(x): round(v, 2) for x, v in (sc2 or {}).items()})
