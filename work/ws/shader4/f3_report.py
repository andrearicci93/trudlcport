"""F3: report finale. Unita' di test = singolo PS (lib Xbox x, slot Xbox xs) non illuminato in pos2 con gemello PC (PC slot k, k&1 == xs, primo occupato).
Campione di 50 con seme fisso + intero insieme."""
import sys, os, random, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
cands = candidates()
items = []
for x, p in cands:
    rs = run_pair(x, p)
    for xs, r in enumerate(rs):
        if r[0] == 'NOPCSLOT': continue
        items.append((x, p, xs, r))
def verdict(r):
    if r[0] != 'OK': return 'FAIL:' + r[0]
    ok = r[1] >= 0.95
    d = r[2]
    return 'PASS' if ok and d['consts_eq'] and d['samp_eq'] and d['dcl_eq'] else ('PASS-num-only' if ok else 'FAIL:num')
random.seed(20261013)
sample = random.sample(items, min(50, len(items)))
def verdictB(r):
    if r[0] != 'OK': return 'FAIL'
    d = r[2]
    strip = lambda m: {k: v for k, v in m.items() if 'misc' not in k}
    ok = r[1] >= 0.95 and d['consts_eq'] and d['samp_eq'] and strip(d['tin']) == strip(d['pin'])
    return 'PASS' if ok else 'FAIL'
def summarize(its, label):
    print('  criterio B (dcl = interpolatori+oC0, vPos/vFace esclusi):', dict(collections.Counter(verdictB(r) for _, _, _, r in its)))
    c = collections.Counter(verdict(r) for _, _, _, r in its)
    print(label, 'n=%d' % len(its), dict(c))
    return c
c1 = summarize(sample, 'CAMPIONE 50 (seme 20261013)')
c2 = summarize(items, 'INSIEME completo')
print('\nTabella dei non PASS (insieme completo):')
for x, p, xs, r in items:
    v = verdict(r)
    if v != 'PASS':
        print(' ', x, p, 'slot', xs, v, (r[1] if r[0] == 'OK' else r[1]), (r[2]['ct'], r[2]['cp']) if r[0] == 'OK' and not r[2]['consts_eq'] else '')
json.dump([(x, p, xs, verdict(r), (r[1] if r[0] == 'OK' else None)) for x, p, xs, r in items], open(os.path.join(HERE, 'f3_report.json'), 'w'))
