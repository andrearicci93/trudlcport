"""Convert every DLC Mesh section (type 12 with 'Mesh' magic) with mesh_convert and check structural validity
+ geometric self-consistency (converted triangles == Xbox triangles, bones resolved through palettes).
usage: tools/venv/bin/python -I tools/mesh_dlc.py  -> work/render/mesh_dlc.txt"""
import sys, os, pickle, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesh_convert as MC, mesh_validate as MV
from mesh_tr8 import Mesh, H
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')

def xbox_tri_keys(d):
    """Geometric triangle multiset straight from the Xbox section (positions swapped to LE, uv swap16,
    skin = global bones + weights in PC byte order) for comparison with MV.tri_keys(pc, 'geo')."""
    m = Mesh(d, 'be'); idx = m.indices(); C = collections.Counter(); gi = 0
    for b in m.meshes:
        groups = m.groups[gi:gi + b['numGroups']]; gi += b['numGroups']
        if not b['vf']: continue
        st = b['vf']['stride']; base = H + b['vdataOff']
        el = [(s, o, t) for s, o, t, _ in b['vf']['elems']]
        ws = [o for s, o, t in el if s == 0x48E691C0]
        def vkey(v):
            a = base + v * st; k = []
            for s, o, t in el:
                if s not in MV.GEO: continue
                if s == 0x5156D8D3:
                    ii = d[a + o + 1:a + o + 4] + d[a + o:a + o + 1]
                    w = (d[a + ws[0] + 1:a + ws[0] + 4] + d[a + ws[0]:a + ws[0] + 1]) if ws else b'\xff' * 4
                    k.append(tuple(sorted((i, ww) for i, ww in zip(ii, w) if ww)))
                elif s == 0x48E691C0:
                    k.append(d[a + o + 1:a + o + 4] + d[a + o:a + o + 1])
                elif t == 0x13:
                    x = d[a + o:a + o + 4]; k.append(bytes((x[1], x[0], x[3], x[2])))
                else:
                    n = {2: 12, 3: 16, 1: 8}.get(t, 4)
                    k.append(b''.join(d[a + o + j:a + o + j + 4][::-1] for j in range(0, n, 4)))
            return tuple(k)
        for g in groups:
            for t in range(g['numTris']):
                tr = idx[g['baseIndex'] + 3 * t:g['baseIndex'] + 3 * t + 3]
                ks = [vkey(v) for v in tr]; r = min(range(3), key=lambda i: ks[i])
                C[(g['material'], tuple(ks[r:] + ks[:r]))] += 1
    return C

def one(job):
    key, s = job
    st = collections.Counter(); info = {}
    try:
        pd, pr = MC.convert(s['data'], s['reloc'], None, info)
    except Exception as e:
        return key, s['id'], dict(error=repr(e)[:200])
    v = MV.validity(pd, pr)
    r = dict(valid=not v, problems=v, rebatched=info['rebatched'], unknown_decls=info['unknown_decls'], max_palette=info['max_palette'],
             size_x=len(s['data']), size_pc=len(pd))
    mx = Mesh(s['data'], 'be')
    if mx.numMeshes:
        r['geo_equal'] = xbox_tri_keys(s['data']) == MV.tri_keys(pd, 'geo')
    else:
        r['geo_equal'] = True
    return key, s['id'], r

if __name__ == '__main__':
    from multiprocessing import Pool
    dlc = pickle.load(open(W + '/render/dlc_render.pkl', 'rb'))
    jobs = []; seen = set()
    for path, i, h, secs in dlc:
        for s in secs or []:
            if s['type'] == 12 and s['data'][0x10:0x14] == b'hseM' and s['id'] not in seen:
                seen.add(s['id']); jobs.append(((os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path), h, s['i']), s))
    with Pool(8) as p: out = p.map(one, jobs, chunksize=2)
    T = collections.Counter(); bad = []
    for key, sid, r in out:
        if 'error' in r: T['error'] += 1; bad.append((key, sid, r)); continue
        T['n'] += 1; T['valid'] += r['valid']; T['geo_equal'] += r['geo_equal']; T['rebatched'] += r['rebatched']
        T['unknown_decl_batches'] += r['unknown_decls']; T['meshes_with_unknown_decl'] += r['unknown_decls'] > 0
        if not r['valid'] or not r['geo_equal']: bad.append((key, sid, r))
    lines = ['DLC unique Mesh sections: %d' % len(jobs)] + ['  %-28s %d' % kv for kv in sorted(T.items())]
    lines += ['problems:'] + ['  ' + repr(b)[:300] for b in bad[:50]]
    txt = '\n'.join(lines); print(txt); open(W + '/render/mesh_dlc.txt', 'w').write(txt + '\n')
