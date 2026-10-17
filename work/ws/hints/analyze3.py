# Separa: slot assenti in DLC1 (offset 0), stringhe vuote, conflitti reali (testo non vuoto e diverso). Sola lettura.
import pickle, collections, json
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
S = lambda src, s: T[src][s]['strings']
O = lambda src, s: T[src][s]['offs']
def dec(b): return b.decode('utf-8', 'replace')
out = collections.defaultdict(dict)
cnt = collections.Counter()
for s in SPECS:
    X, U, P = S('xbase', s), S('tu', s), S('pack10', s)
    OP, OU = O('pack10', s), O('tu', s)
    for i in range(1, len(U)):
        p = P[i] if i < len(P) else None
        u = U[i]
        if i < 1284:
            base = X[i]
            key = 'base'
        else:
            base = None; key = 'new'
        pmiss = (i >= len(P)) or (OP[i] == 0)
        if pmiss: c = 'p10_MISSING_slot'
        elif p == b'': c = 'p10_empty_string'
        elif p == u: c = 'same_as_tu'
        else: c = 'REAL_CONFLICT(p10 text != tu text)'
        if key == 'base' and c == 'same_as_tu' and u == base: continue
        cnt[(LN[s], key, c)] += 1
        if c.startswith('REAL') or c == 'p10_empty_string' or (key == 'base' and c != 'same_as_tu' and p != base and not pmiss):
            out[i].setdefault('langs', {})[LN[s]] = {'class': c, 'base': dec(base) if base is not None else None,
                                                    'dlc1': dec(p) if p is not None else None, 'tu': dec(u)}
for k in sorted(cnt): print(k, cnt[k])
real = sorted(i for i in out if any(v['class'].startswith('REAL') for v in out[i]['langs'].values()))
print('REAL conflict indices (any lang):', len(real), real)
emp = sorted(i for i in out if any(v['class'] == 'p10_empty_string' for v in out[i]['langs'].values()))
print('p10 empty-string indices:', len(emp), emp)
json.dump({str(i): out[i] for i in sorted(out)}, open('/path/to/trudlcport/work/ws/hints/conflicts_all.json', 'w'), ensure_ascii=False, indent=1)
for i in real[:200]:
    v = out[i]['langs']; l0 = v.get('L0') or next(iter(v.values()))
    print(i, '| L0 dlc1:', repr(l0['dlc1'][:70]), '| L0 tu:', repr(l0['tu'][:70]))
