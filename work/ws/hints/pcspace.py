# Interpreta gli indici richiesti come id PC o come indici Xbox/TU: mappa inversa da locmap (sola lettura).
import sys, pickle, json
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
V = {src: {s: (T[src][s]['lang'], T[src][s]['strings']) for s in T[src]} for src in T}
L.files_cache['pcpatch'] = {s: T['pcpatch'][s]['raw'] for s in T['pcpatch']}
m, info = L.build_map(V)
inv = {}
for x, p in m.items(): inv.setdefault(p, []).append(x)
S0 = 0xfffff7e1
d = lambda b: b.decode('utf-8', 'replace')[:45]
req = [1288, 1289] + list(range(1291, 1298)) + list(range(1316, 1376))
PC = T['pcpatch'][S0]['strings']; PCO = T['pcpatch'][S0]['offs']
ok = 0; rows = []
for p in req:
    xs = inv.get(p, [])
    pc_missing = PCO[p] == 0 if p < len(PCO) else True
    rows.append((p, 'MISSING' if pc_missing else d(PC[p]), xs))
for r in rows: print('pcid', r[0], 'pc_L0', repr(r[1]), 'xbox_idx', r[2])
print('n requested', len(req), 'with xbox preimage', sum(1 for r in rows if r[2]))
json.dump({'inv_present': {str(p): inv.get(p, []) for p in req}}, open('/path/to/trudlcport/work/ws/hints/pcid_inverse_req.json', 'w'))
