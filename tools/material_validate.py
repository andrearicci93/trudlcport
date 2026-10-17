"""Validate material_convert on Xbox<->PC base pairs (unique material ids, matched by material id map).
usage: python3 -I tools/material_validate.py"""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material_convert as MC
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
res = pickle.load(open(W + '/render/pairs_render.pkl', 'rb'))
mx2p = pickle.load(open(W + '/render/material_x2p.pkl', 'rb'))
sx2p = pickle.load(open(W + '/render/shader_x2p.pkl', 'rb'))
gid = json.load(open(W + '/generic/idmap.json'))
tmap = {int(k): v for k, v in gid['5'].items()}
st = collections.Counter(); seen = set(); bad = []
def diffbytes(a, b): return sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
for nm, X, P in res:
    for a, b in zip(X, P):
        if a['type'] != 10 or b['type'] != 10 or mx2p.get(a['id']) != b['id'] or a['id'] in seen: continue
        seen.add(a['id'])
        pd, pr = MC.convert(a['data'], a['reloc'], lambda i: sx2p.get(i, i), lambda i: tmap.get(i, i))
        st['n'] += 1
        same_n = struct.unpack_from('>I', a['data'], 0x58)[0] == struct.unpack_from('<I', b['data'], 0x58)[0]
        st['params-count-equal'] += same_n
        ex = pd == b['data']; st['data-exact'] += ex; st['reloc-exact'] += pr == b['reloc']
        if same_n: st['n-samecount'] += 1; st['data-exact-samecount'] += ex
        if not ex:
            # mask params block to see if only params differ
            st['diffbytes'] += diffbytes(pd, b['data'])
            if len(bad) < 400: bad.append((nm, a['id'], diffbytes(pd, b['data']), [o for o in range(0, min(len(pd), len(b['data'])), 4) if pd[o:o+4] != b['data'][o:o+4]][:8]))
print(dict(st))
c = collections.Counter(tuple(x[3][:2]) for x in bad); print(c.most_common(15))
print(bad[:10])
