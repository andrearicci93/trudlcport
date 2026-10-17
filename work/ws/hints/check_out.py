# Verifiche sul candidato: testi campione, indici senza testo DLC1, fascia base, 'Unavailable' nel base PC. Sola lettura.
import sys, pickle, os, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
H = '/path/to/trudlcport/work/ws/hints'
T = pickle.load(open(H + '/tables.pkl', 'rb'))
dv = pickle.load(open(H + '/dlc1_var.pkl', 'rb')); var_x, Q = dv['var_x'], dv['Q']
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
def sfx(s): return (s & 0x1f) if s != 0xffffffe0 else 32
def present(src, s, x): return x < len(T[src][s]['offs']) and x != 0 and T[src][s]['offs'][x] != 0
cand = {s: L.parse(open(os.path.join(H, 'out', 'locals.bin_%03d' % sfx(s)), 'rb').read(), 'le')[1] for s in SPECS}
# 1) samples L0 and L4 (ES)
for x in [1288, 1291, 1292, 1316, 1317, 1326, 1373]:
    if x not in Q: print('x', x, 'not a variant (pack1 missing or same as TU)'); continue
    for s in [0xfffff7e1, 0xfffff7f0]:
        print('x %d -> pc %d %s | DLC1 cand=%r | TU/DLC2=%r' % (x, Q[x], 'L0' if s == 0xfffff7e1 else 'L4', cand[s][Q[x]][:45], (T['tu'][s]['strings'][x][:45] if present('tu', s, x) else '<MISS>')))
# 2) DLC1-index without DLC1 text: pack1 missing, pack10 missing/unused, TU text present -> DLC2 text would leak
leak = []
for x in range(1284, 1407):
    if any(present('tu', s, x) for s in SPECS) and not any(present('pack1', s, x) for s in SPECS):
        leak.append(x)
print('indices 1284..1406 with TU/DLC2 text and NO pack1 (DLC1) text:', len(leak), leak)
refs_dlc1 = [1288, 1291, 1292, 1293, 1294, 1295, 1296, 1297] + list(range(1316, 1376))
print('of which referenced by DLC1 script 74 (any 1288-1297/1316-1375 id):', [x for x in refs_dlc1 if x in leak])
# 3) base range: pack1 vs base and vs TU differences (x < 1284)
bdiff = [x for x in range(1, 1284) if any(present('pack1', s, x) and T['pack1'][s]['strings'][x] != T['xbase'][s]['strings'][x] for s in SPECS)]
print('base-range x where pack1 differs from base (any lang):', len(bdiff), bdiff[:40])
# 4) 'Unavailable' in base PC (pcpatch) and in merged candidate
for s in [0xfffff7e1]:
    pc = T['pcpatch'][s]['strings']
    ids = [i for i, t in enumerate(pc) if t == b'Unavailable']
    print('pcpatch L0 ids with text Unavailable:', len(ids), ids[:20], ' candidate text at 457:', cand[s][457][:40])
