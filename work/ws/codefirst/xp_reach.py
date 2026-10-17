"""Regola di RAGGIUNGIBILITA': una lane PC che raggiunge le uscite del blocco luci deve avere come sorgente una lane Xbox che raggiunge le uscite del blocco Xbox.
Validazione su tutte le lane risolte per valore (kind 'lane'); poi uso come filtro dei pareggi."""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from xp_struct import *
fam = [(981, 1531), (111, 225), (300, 356), (164, 207), (1409, 1038), (1431, 1060)]
tot = ok = 0
for xs, pd in fam:
    C, res, ties, out, _, _ = struct_scores(xs, pd)
    CP, CX = out[(1, 2)]
    for l, (kind, val) in sorted(res.items()):
        if kind != 'lane' or l not in CP: continue
        tot += 1; good = tuple(val) in CX; ok += good
        if not good: print('  VIOLAZIONE (%d,%d) PC c%d.%s <- Xbox c%d.%s non raggiunge le uscite Xbox' % (xs, pd, l[0], 'xyzw'[l[1]], val[0], 'xyzw'[val[1]]))
    print('(%d,%d): lane PC raggiungenti %d; lane Xbox raggiungenti %d: %s' % (xs, pd, len([l for l in res if l in CP]), len(CX), sorted('c%d.%s' % (x[0], 'xyzw'[x[1]]) for x in CX)))
print('regola di raggiungibilita: %d/%d lane risolte per valore la rispettano' % (ok, tot))
