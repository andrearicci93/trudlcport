"""Impara dalle coppie base (x2p) la mappa nome CTAB -> registro PC (costanti float, bool, sampler) e la confronta con il registro Xbox."""
import sys, os, pickle, collections, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'work/ws/xenos')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import sm3dis, shaderlib
L = pickle.load(open(os.path.join(ROOT, 'work/render/shaderlibs.pkl'), 'rb'))
x2p = pickle.load(open(os.path.join(ROOT, 'work/render/shader_x2p.pkl'), 'rb'))
X, P = L['X'], L['P']
pc = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))   # set -> name -> Counter((reg,count))
xb = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
cmp_ = collections.defaultdict(collections.Counter)                                   # (set) -> Counter(equal?)
diffs = collections.defaultdict(collections.Counter)
for x, p in x2p.items():
    px = {}; pp = {}
    for s in X[x]['slots']:
        if s == 0xffffffff: continue
        v, ct = shaderlib.constants(X[x]['entries'][s]['blob'], 'x')
        for n, rs, ri, rc in ct: px[(n, rs)] = (ri, rc); xb[rs][n][(ri, rc)] += 1
    for s in P[p]['slots']:
        if s == 0xffffffff: continue
        b = P[p]['entries'][s]['blob']
        for n, rs, ri, rc in sm3dis.ctab_of(b[:sm3dis.bytecode_len(b)]):
            pp[(n, rs)] = (ri, rc); pc[rs][n][(ri, rc)] += 1
    for k in set(px) & set(pp):
        cmp_[k[1]][px[k] == pp[k]] += 1
        if px[k] != pp[k]: diffs[k[1]][(k[0] if not k[0].startswith('p_') else 'p_*', px[k], pp[k])] += 1
print('registro uguale Xbox/PC per nome (set: 0 bool,1 int,2 float,3 sampler):', {k: dict(v) for k, v in cmp_.items()})
for rs in diffs:
    print('set', rs, 'differenze (nome, xbox(reg,count), pc(reg,count)): top'); 
    for k, v in diffs[rs].most_common(25): print('  ', v, k)
# nomi PC con piu' di un registro
multi = {rs: {n: dict(c) for n, c in d.items() if len(c) > 1} for rs, d in pc.items()}
for rs, d in multi.items(): print('PC set', rs, 'nomi con >1 registro:', len(d), list(d.items())[:5])
print('PC nomi per set:', {rs: len(d) for rs, d in pc.items()})
json.dump({str(rs): {n: sorted(c.items()) for n, c in d.items()} for rs, d in pc.items()}, open(os.path.join(HERE, 'pc_ctab_names.json'), 'w'), indent=0)

# tabella per posizione: costanti float dei PC libs in posizione 2 (8 slot) separata
import struct
pos = collections.defaultdict(set)
XM, PM = L['XM'], L['PM']
mx2p = pickle.load(open(os.path.join(ROOT, 'work/render/material_x2p.pkl'), 'rb'))
for mid, (d, r) in XM.items():
    if mid not in mx2p or mx2p[mid] not in PM: continue
    pt = struct.unpack_from('<4I', PM[mx2p[mid]][0], 0x28)
    for i in range(3):
        if pt[i]: pos[pt[i]].add(i)
tab = {0: collections.defaultdict(collections.Counter), 1: collections.defaultdict(collections.Counter), 2: collections.defaultdict(collections.Counter)}
for p_, ps in pos.items():
    if p_ not in P or P[p_]['kind'] != 1: continue
    for s in set(P[p_]['slots']):
        if s == 0xffffffff: continue
        b = P[p_]['entries'][s]['blob']
        for n, rs, ri, rc in sm3dis.ctab_of(b[:sm3dis.bytecode_len(b)]):
            if rs == 2:
                for q in ps: tab[q][n][(ri, rc)] += 1
out = {str(q): {n: sorted(c.items(), key=lambda kv: -kv[1]) for n, c in d.items()} for q, d in tab.items()}
json.dump(out, open(os.path.join(HERE, 'pc_ctab_by_pos.json'), 'w'))
for q in (0, 1, 2):
    print('pos', q, 'nomi', len(tab[q]), {n: [k for k, v in c.most_common(3)] for n, c in tab[q].items() if n in ('MaterialParams', 'InstanceParams', 'GlobalParams', 'MaterialOpacity', 'AlphaThreshold')})
