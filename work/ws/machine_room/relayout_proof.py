"""relayout_proof.py - (19/11/2026) solo lettura. Prova della regola fxrelayout sul base (work/generic/store.pkl): ogni DTP
tabella-di-record Xbox (relayout_scan.table) ricostruito a passo 0x28 (relayout_scan.rec, id via idmap) == byte PC del base?"""
import sys, pickle, collections, struct
sys.argv = [sys.argv[0], 'B277_lukas']
sys.path.insert(0, '/path/to/trudlcport/work/ws/machine_room')
import importlib.util
spec = importlib.util.spec_from_file_location('rs', '/path/to/trudlcport/work/ws/machine_room/relayout_scan.py')
src = open(spec.origin, encoding='utf-8').read().split('tot = collections.Counter()')[0]   # solo le funzioni
ns = {}; exec(compile(src, spec.origin, 'exec'), ns)
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb')); im = ns['im7']
xids = {i for (t, i) in S['xb_store'] if t == 7}
class Sx: pass
c = collections.Counter()
for (t, xid), xs in sorted(S['xb_store'].items()):
    if t != 7: continue
    x = Sx(); x.data = xs['data']; x.reloc = xs['reloc']
    tt = ns['table'](x, xids)
    if not tt: continue
    n, P = tt; p = S['pc_store'].get((7, im.get(xid, xid)))
    if not p or len(p['data']) != len(x.data): c['senza coppia'] += 1; continue
    ids = [struct.unpack_from('>I', x.data, P + 0x24 * j + 0x14)[0] for j in range(n)]
    new = b''.join(ns['rec'](x.data, P + 0x24 * j, im.get(ids[j], ids[j])) for j in range(n))
    cur = p['data'][P:P + 0x28 * n]
    k = 'uguale' if cur == new else ('uguale salvo id' if all(cur[q:q + 0x14] == new[q:q + 0x14] and cur[q + 0x18:q + 0x28] == new[q + 0x18:q + 0x28] for q in range(0, 0x28 * n, 0x28)) else 'DIVERSO')
    c[k] += 1
    if k != 'uguale': print(xid, n, hex(P), k, '\n   pc ', cur.hex(), '\n   new', new.hex())
print(dict(c))
