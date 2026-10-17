"""One-off: shrink work/generic/mask_table.pkl (Counter per key, 789MB) to {key: best class} for conversion-time use."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generic_learn as G
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
v, n = pickle.load(open(os.path.join(W, 'mask_table.pkl'), 'rb'))
T = G.Table(); T.v.update(v)
best = {}
for k in list(v.keys()):
    b = T.best(k)
    if b is not None: best[k] = b
pickle.dump(best, open(os.path.join(W, 'mask_table_best.pkl'), 'wb'), protocol=4)
print('keys', len(v), 'slim', len(best), flush=True)
