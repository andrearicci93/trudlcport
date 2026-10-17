# Classifica ogni indice di stringa (base 0..1283, DLC-new 1284..1406) per lingua. Sola lettura.
import sys, pickle, collections, json
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
import importlib.util
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
S = lambda src, s: T[src][s]['strings']
def cls(i, s):
    X = S('xbase', s); U = S('tu', s); P = S('pack10', s)
    x = X[i] if i < len(X) else None; u = U[i] if i < len(U) else None; p = P[i] if i < len(P) else None
    if i < 1284:
        if p is None: return 'base-no-p10'
        if p == x and u == x: return 'A_same'
        if p == u and p != x: return 'C_dlc1=tu!=base'
        if p != x and u == x: return 'B_dlc1_changes_base_tu_keeps'
        if p == x and u != x: return 'E_dlc1=base,tu_changes'
        return 'D_CONFLICT_base_range(p10!=tu!=base)'
    else:
        if p is None: return 'G_tu_only(idx>=p10_n)'
        if p == u: return 'F_same_new'
        return 'F_CONFLICT_dlc_new(p10!=tu)'
cats = collections.Counter(); per_lang = {}
idxs = {}
n = max(len(S('tu', s)) for s in SPECS)
for s in SPECS:
    per_lang[LN[s]] = collections.Counter()
    for i in range(n):
        c = cls(i, s)
        per_lang[LN[s]][c] += 1
        if c[0] in 'BDEF' and 'same' not in c:
            idxs.setdefault(c, set()).add(i)
for L_ in per_lang: print(L_, dict(per_lang[L_]))
print('indices by category (union over langs):')
for c in sorted(idxs):
    v = sorted(idxs[c]); print(c, len(v), v[:80])
# hint indices requested
req = [1288] + list(range(1291, 1298)) + list(range(1316, 1376))
print('requested hint idx count', len(req), 'max', max(req), 'pack10 n', len(S('pack10', SPECS[0])))
