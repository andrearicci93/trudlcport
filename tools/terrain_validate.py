"""Learn the Y-record hash table and validate terrain_convert on all base pairs.
Tiers: exact; struct-exact (all words outside vertex/index data); semantic (per BVH slot, multiset of triangles
(Y hash + Y u16/u8 fields, vertex bytes) equal between converted and PC); valid (all draw-list ranges in bounds).
usage: tools/venv/bin/python -I tools/terrain_validate.py  -> work/render/terrain_validate.txt"""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terrain_convert as TC
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')

def tri_set(d, e):
    T = TC.parse(d, e); H = T['H']
    idx = struct.unpack_from(e + '%dH' % T['nIdx'], d, H + T['offIdx'])
    C = collections.Counter()
    for slot, seq, ents in TC.draw_lists(d, T, e):
        for yi, cnt, start in ents:
            Y = T['Y'][yi]; vb = T['vbs'][Y[1]]; vf = T['vfs'][vb[3]]; st = vf['stride']; base = H + vb[0]
            ykey = (d[H + T['offY'] + 32 * yi + 8:H + T['offY'] + 32 * yi + 12], Y[3], Y[4], Y[5])
            for t in range(0, cnt, 3):
                ks = [d[base + v * st:base + (v + 1) * st] for v in idx[start + t:start + t + 3]]
                r = min(range(3), key=lambda i: ks[i])
                C[(slot, ykey, tuple(ks[r:] + ks[:r]))] += 1
    return C

def valid(d, e):
    try:
        T = TC.parse(d, e); H = T['H']
        idx = struct.unpack_from(e + '%dH' % T['nIdx'], d, H + T['offIdx'])
        for slot, seq, ents in TC.draw_lists(d, T, e):
            for yi, cnt, start in ents:
                if yi >= T['nY'] or start + cnt > T['nIdx'] or cnt % 3: return False
                vbi = T['Y'][yi][1]
                if vbi >= T['nVB']: return False
                vb = T['vbs'][vbi]
                if vb[3] >= T['nVF'] or H + vb[0] + vb[2] * T['vfs'][vb[3]]['stride'] > len(d): return False
                seg = idx[start:start + cnt]
                if seg and max(seg) >= vb[2]: return False
        return True
    except Exception:
        return False

_ids = None
def IDS(t, x):
    global _ids
    if _ids is None:
        gid = json.load(open(W + '/generic/idmap.json')); gm = {int(t): {int(a): b for a, b in v.items()} for t, v in gid.items()}
        mx2p = pickle.load(open(W + '/render/material_x2p.pkl', 'rb'))
        _ids = (gm, mx2p)
    gm, mx2p = _ids
    return mx2p.get(x, x) if t == 10 else gm.get(t, {}).get(x, x)

if __name__ == '__main__':
    res = pickle.load(open(W + '/render/pairs_render.pkl', 'rb'))
    seen = set(); pairs = []
    for nm, X, P in res:
        for a, b in zip(X, P):
            if a['type'] == 12 and b['type'] == 12 and TC.is_terrain(a['data']) and a['id'] not in seen:
                seen.add(a['id']); pairs.append((nm, a, b))
    del res
    ym = collections.defaultdict(collections.Counter)
    for nm, a, b in pairs:
        if a['size'] != b['size']: continue
        T = TC.parse(a['data']); TP = TC.parse(b['data'], '<')
        # Y records may be reordered on PC: pair them by (u16,u8,u8 + idx) when equal count, else by position
        for k in range(T['nY']):
            r = T['H'] + T['offY'] + 32 * k
            ym[bytes(a['data'][r + 8:r + 12])][bytes(b['data'][r + 8:r + 12])] += 1
    m = {k: v.most_common(1)[0][0] for k, v in ym.items()}
    pickle.dump(m, open(W + '/render/terrain_yhash.pkl', 'wb')); TC._YHASH = m
    st = collections.Counter(); bad = []
    for nm, a, b in pairs:
        st['n'] += 1
        s = {}
        pd, pr = TC.convert(a['data'], a['reloc'], IDS, s)
        st['valid'] += valid(pd, '<'); st['PC valid'] += valid(b['data'], '<')
        if a['size'] != b['size']: st['size differs'] += 1; bad.append((nm, a['i'], 'size')); continue
        st['exact'] += pd == b['data']; st['reloc_exact'] += pr == b['reloc']
        T = TC.parse(a['data']); H = T['H']
        skip = [(H + T['offIdx'], H + T['offIdx'] + 2 * T['nIdx'])] + [(H + v[0], H + v[0] + v[2] * T['vfs'][v[3]]['stride']) for v in T['vbs']]
        inskip = lambda o: any(x <= o < y for x, y in skip)
        nbs = sum(1 for o in range(0, len(pd), 4) if pd[o:o + 4] != b['data'][o:o + 4] and not inskip(o))
        st['struct_exact'] += nbs == 0
        sem = tri_set(pd, '<') == tri_set(b['data'], '<')
        st['semantic'] += sem
        if not sem:
            A = tri_set(pd, '<'); B = tri_set(b['data'], '<')
            # looser: ignore slot (PC may re-partition the BVH) and Y fields
            la = collections.Counter(k[2] for k in A.elements()); lb = collections.Counter(k[2] for k in B.elements())
            st['semantic-ignoring-slot/Y'] += la == lb
            bad.append((nm, a['i'], 'tris %d/%d common %d' % (sum(A.values()), sum(B.values()), sum((A & B).values())), 'loose-eq' if la == lb else 'loose-common %d' % sum((la & lb).values())))
        if s.get('yhash_unknown'): st['yhash_unknown_records'] += s['yhash_unknown']
    lines = ['terrain pairs (unique Xbox ids): %d' % len(pairs)] + ['  %-34s %d' % kv for kv in sorted(st.items())]
    lines += ['non-semantic: %d' % len(bad)] + ['  ' + repr(x) for x in bad]
    txt = '\n'.join(lines); print(txt); open(W + '/render/terrain_validate.txt', 'w').write(txt + '\n')
