"""Pareggi residui: scelta guidata dall'ORACOLO PC. Per ogni assegnazione iniettiva dei candidati ai lane in pareggio costruisce T per ogni coppia base
della classe e confronta col PC vero (luci accese/spente/miste, tutti i materiali ponte). Sceglie l'assegnazione col maggior numero di coppie >= 0.99.
Uso: resolve_ties.py XS PD -> tabella assegnazione x coppie."""
import sys, itertools
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *


def assignments(ties):
    lanes = sorted(ties)
    for combo in itertools.product(*[ties[l] for l in lanes]):
        if len(set(combo)) == len(combo): yield dict(zip(lanes, combo))


def score_all(xs, pd, res, pairs, nmat=99):
    out = {}
    for xb, pb in pairs:
        try:
            o, info, n = one_pair(xb, pb, xs, pd, res, nmat=nmat)
            out[(xb, pb)] = min(o.values())
        except Exception as e:
            out[(xb, pb)] = -1.0
    return out


def run(xs, pd):
    res, ties = mp_resolve.resolve(xs, pd)
    pairs = [(xs, pd)] + [(a, b) for a, b in find_donors('X', xs, 0, want=60) if (a, b) != (xs, pd)]
    rows = []
    for asg in (assignments(ties) if ties else [{}]):
        r2 = dict(res)
        for l, x in asg.items(): r2[l] = ('lane', x)
        sc = score_all(xs, pd, r2, pairs)
        good = sum(1 for v in sc.values() if v >= 0.99)
        rows.append((good, asg, sc)); print('  asg', {('c%d.%s' % (l[0], 'xyzw'[l[1]])): ('c%d.%s' % (x[0], 'xyzw'[x[1]])) for l, x in asg.items()}, '-> %d/%d' % (good, len(sc)), {k: round(v, 3) for k, v in sc.items() if v < 0.99}, flush=True)
    best = max(rows, key=lambda r: r[0])
    return best, rows


if __name__ == '__main__':
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    print('=== (%d,%d)' % (xs, pd), flush=True)
    best, rows = run(xs, pd)
    print('MIGLIORE: %d/%d' % (best[0], len(best[2])), best[1])
