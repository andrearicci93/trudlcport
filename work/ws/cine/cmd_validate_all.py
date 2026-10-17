"""Valida cine_cmd su TUTTE le coppie DTP base (work/script/pairs_7.pkl): parole non-id/non-ptr uguali al PC."""
import sys, os, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine_cmd as CC, cinepairs
sys.path.insert(0, cinepairs.T)
import drm_reloc as R
P = pickle.load(open(os.path.join(cinepairs.T, '..', 'work', 'script', 'pairs_7.pkl'), 'rb'))
tot = collections.Counter(); bad = []; seen = set()
for q in P:
    d = q['xd']
    if CC.fmt_of(d) is None or len(d) != len(q['pd']) or d in seen: continue
    seen.add(d)
    r = R.parse(q['xr'], 'be')
    try: o, cl = CC.convert(d, None, {a for a, _ in r.internal})
    except ValueError as e: tot['non_struttura'] += 1; continue
    nw = 0
    for k in range(0, len(d) - 3, 4):
        if cl.get(k) in ('id', 'ptr') or k in {a for a, _ in r.internal}: continue
        tot['parole'] += 1
        if o[k:k + 4] != q['pd'][k:k + 4]:
            nw += 1
            if len(bad) < 15: bad.append((q['name'].split('\\')[-1], hex(k), cl.get(k), d[k:k + 4].hex(), o[k:k + 4].hex(), q['pd'][k:k + 4].hex()))
    tot['dtp'] += 1; tot['esatti'] += nw == 0; tot['parole_sbagliate'] += nw
print(dict(tot)); [print('  ', b) for b in bad]
