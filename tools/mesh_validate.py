"""Validate mesh_convert on Xbox<->PC base pairs (Mesh-magic type-12 sections, unique Xbox ids).
Tiers per mesh:
  exact        converted data + reloc byte-identical to PC
  sizeok       same size (then per-region word diffs are tallied)
  sem_strict   same multiset of triangles where a vertex = all element bytes (skin indices resolved through the
               palette to global bones, paired with weights), over the whole mesh (batching-independent)
  sem_loose    same, ignoring NORMAL/TANGENT/BINORMAL bytes (PC re-encoded some normals)
  sem_geo      same, position + texcoords + skin only
  valid        structural validity of the converted mesh (palettes <= 42, indices < numVerts, groups inside
               their batch, offsets in bounds, numIndices consistent)
  tail/lists/header equal (bytes after listsEnd, id lists, header without offsets/counts)
usage: tools/venv/bin/python -I tools/mesh_validate.py [limit]   -> work/render/mesh_validate.txt"""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesh_convert as MC
import drm_reloc as R
from mesh_tr8 import Mesh, SEM, H
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
NRM = {0x36F5E414, 0xF1ED11C3, 0x64A86F01}
GEO = {0xD2F7D823, 0x8317902A, 0x8E54B6F3, 0x8A95AB44, 0x5156D8D3, 0x48E691C0}

def tri_keys(d, mode):
    """Counter of canonical triangles over the mesh; mode 'strict'|'loose'|'geo'."""
    m = Mesh(d, 'le'); idx = m.indices(); C = collections.Counter()
    gi = 0
    for b in m.meshes:
        groups = m.groups[gi:gi + b['numGroups']]; gi += b['numGroups']
        if not b['vf']: continue
        st = b['vf']['stride']; base = H + b['vdataOff']
        pal = list(struct.unpack_from('<%dI' % b['skinSize'], d, H + b['skinOff'])) if b['skinSize'] else None
        el = [(s, o, t) for s, o, t, _ in b['vf']['elems']]
        ws = [o for s, o, t in el if s == 0x48E691C0]
        cache = {}
        def vkey(v):
            if v in cache: return cache[v]
            a = base + v * st; k = []
            for s, o, t in el:
                if mode == 'loose' and s in NRM: continue
                if mode == 'geo' and s not in GEO: continue
                if s == 0x5156D8D3:
                    ii = d[a + o:a + o + 4]
                    w = d[a + ws[0]:a + ws[0] + 4] if ws else b'\xff\xff\xff\xff'
                    k.append(tuple(sorted(((pal[i] if pal and i < len(pal) else ('bad', i)), ww) for i, ww in zip(ii, w) if ww)))
                elif s in NRM:
                    k.append(d[a + o:a + o + 3])   # w byte is padding (127 or 0 on PC, unused by Xbox DEC3N)
                else:
                    n = {2: 12, 3: 16, 1: 8}.get(t, 4)
                    k.append(d[a + o:a + o + n])
            cache[v] = r = tuple(k); return r
        for g in groups:
            for t in range(g['numTris']):
                tr = idx[g['baseIndex'] + 3 * t:g['baseIndex'] + 3 * t + 3]
                ks = [vkey(v) for v in tr]
                r = min(range(3), key=lambda i: ks[i])
                C[(g['material'], tuple(ks[r:] + ks[:r]))] += 1
    return C

def validity(d, rb):
    m = Mesh(d, 'le'); bad = []
    rel = R.parse(rb, 'le')
    if R.check(rel, len(d)): bad.append('reloc bounds')
    if m.numMeshes == 0: return bad
    idx = m.indices()
    if len(idx) != m.numIndices: bad.append('nidx')
    gi = 0
    for b in m.meshes:
        if b['skinSize'] > MC.MAXBONES: bad.append('palette>42')
        if b['vf'] and H + b['vdataOff'] + b['numVerts'] * b['vf']['stride'] > len(d): bad.append('vdata oob')
        groups = m.groups[gi:gi + b['numGroups']]; gi += b['numGroups']
        lo, hi = b['baseIndex'], b['baseIndex'] + 3 * b['numTris']
        for g in groups:
            if not (lo <= g['baseIndex'] and g['baseIndex'] + 3 * g['numTris'] <= hi): bad.append('group outside batch')
            seg = idx[g['baseIndex']:g['baseIndex'] + 3 * g['numTris']]
            if seg and max(seg) >= b['numVerts']: bad.append('index>=numVerts')
        if b['vf'] and b['skinSize']:
            el = {s: o for s, o, t, _ in b['vf']['elems']}
            if 0x5156D8D3 in el:
                st = b['vf']['stride']; base = H + b['vdataOff']; o = el[0x5156D8D3]
                mx = max(max(d[base + v * st + o:base + v * st + o + 4]) for v in range(b['numVerts']))
                if mx >= b['skinSize']: bad.append('skin index >= palette')
    if gi != m.numGroups: bad.append('group count')
    return sorted(set(bad))

def region_of(m, o):
    if o < 0x10: return 'root'
    if o < H + 0x84: return 'hdr'
    for b in m.meshes:
        if b['vf'] and b['vf']['off'] <= o < b['vf']['off'] + 16 + 8 * b['vf']['n']: return 'vdecl'
        if b['vf'] and H + b['vdataOff'] <= o < H + b['vdataOff'] + b['numVerts'] * b['vf']['stride']:
            eo = (o - H - b['vdataOff']) % b['vf']['stride']
            el = [(e, SEM.get(s, hex(s))) for s, e, t, _ in b['vf']['elems'] if e <= eo]
            return 'v:' + max(el)[1] if el else 'v:?'
        if b['skinSize'] and H + b['skinOff'] <= o < H + b['skinOff'] + 4 * b['skinSize']: return 'palette'
    if H + m.meshInfoOff <= o < H + m.meshInfoOff + 52 * m.numMeshes: return 'meshinfo'
    if H + m.faceOff <= o < H + m.faceOff + 2 * m.numIndices: return 'index'
    if H + m.groupOff <= o < H + m.groupOff + 64 * m.numGroups: return 'group'
    if H + m.matOff <= o < m.listsEnd: return 'idlists'
    if o >= m.listsEnd: return 'tail'
    return 'other'

def check_one(job):
    nm, a, b, ids_ok = job
    st = collections.Counter(); regs = collections.Counter(); ex = []
    info = {}
    try:
        pd, pr = MC.convert(a['data'], a['reloc'], IDS, info)
    except Exception as e:
        st['convert-error'] += 1; return nm, a['i'], st, regs, [repr(e)[:200]]
    mx = Mesh(a['data'], 'be'); mp = Mesh(b['data'], 'le'); mc = Mesh(pd, 'le')
    st['n'] += 1
    st['pc-rebatched'] += mx.numMeshes != mp.numMeshes
    st['we-rebatched'] += info['rebatched']
    st['same-batching'] += mc.numMeshes == mp.numMeshes and [x['numTris'] for x in mc.meshes] == [x['numTris'] for x in mp.meshes]
    st['exact'] += pd == b['data']
    st['reloc-exact'] += pr == b['reloc']
    st['exact+reloc'] += pd == b['data'] and pr == b['reloc']
    st['sizeok'] += len(pd) == len(b['data'])
    st['tail-equal'] += pd[mc.listsEnd:] == b['data'][mp.listsEnd:]
    st['lists-equal'] += pd[H + mc.matOff:mc.listsEnd] == b['data'][H + mp.matOff:mp.listsEnd]
    st['hdr-equal'] += pd[0x10:0x10 + 0x6C] == b['data'][0x10:0x10 + 0x6C]
    v = validity(pd, pr)
    st['valid'] += not v
    for x in v: st['invalid:' + x] += 1
    pcv = validity(b['data'], b['reloc'])
    for x in pcv: st['PC-invalid:' + x] += 1
    if mx.numMeshes:
        for mode in ('strict', 'loose', 'geo'):
            ok = tri_keys(pd, mode) == tri_keys(b['data'], mode)
            st['sem_' + mode] += ok
            if ok: break   # stricter implies looser
        else:
            mode = None
        if st['sem_strict']: st['sem_loose'] += 1; st['sem_geo'] += 1
        elif st['sem_loose']: st['sem_geo'] += 1
    else:
        st['empty-mesh'] += 1; st['sem_strict'] += 1; st['sem_loose'] += 1; st['sem_geo'] += 1
    if len(pd) == len(b['data']) and pd != b['data']:
        for o in range(0, len(pd), 4):
            if pd[o:o + 4] != b['data'][o:o + 4]:
                r = region_of(mp, o); regs[r] += 1
                if len(ex) < 6: ex.append((r, hex(o), pd[o:o + 4].hex(), b['data'][o:o + 4].hex()))
    return nm, a['i'], st, regs, ex

_gm = _mx2p = None
def IDS(t, x):
    """Xbox id -> PC id (materials: material_x2p.pkl, others: generic idmap). Lazy (spawned workers)."""
    global _gm, _mx2p
    if _gm is None:
        gid = json.load(open(W + '/generic/idmap.json')); _gm = {int(t): {int(a): b for a, b in v.items()} for t, v in gid.items()}
        _mx2p = pickle.load(open(W + '/render/material_x2p.pkl', 'rb'))
    return _mx2p.get(x, x) if t == 10 else _gm.get(t, {}).get(x, x)
if __name__ == '__main__':
    from multiprocessing import Pool
    res = pickle.load(open(W + '/render/pairs_render.pkl', 'rb'))
    jobs = []; seen = set()
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    for nm, X, P in res:
        for a, b in zip(X, P):
            if a['type'] != 12 or b['type'] != 12 or a['data'][0x10:0x14] != b'hseM' or a['id'] in seen: continue
            seen.add(a['id']); jobs.append((nm, a, b, True))
    del res
    jobs = jobs[:lim]
    with Pool(8) as p: out = p.map(check_one, jobs, chunksize=4)
    T = collections.Counter(); RG = collections.Counter(); bad = []
    for nm, i, st, regs, ex in out:
        T.update(st); RG.update(regs)
        if not st.get('sem_geo') or st.get('convert-error') or any(k.startswith('invalid') for k in st):
            bad.append((nm, i, dict(st), ex))
    lines = ['mesh pairs (unique Xbox ids): %d' % len(jobs)]
    for k in sorted(T): lines.append('  %-40s %d' % (k, T[k]))
    lines.append('word diffs by region (same-size, non-exact):')
    for r, n in RG.most_common(): lines.append('  %-20s %d' % (r, n))
    lines.append('failures (no geometric equivalence / errors / invalid): %d' % len(bad))
    for x in bad[:60]: lines.append('  ' + repr(x)[:400])
    txt = '\n'.join(lines); print(txt)
    open(W + '/render/mesh_validate.txt', 'w').write(txt + '\n')
