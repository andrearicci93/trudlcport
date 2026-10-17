"""TR8 Mesh section (type 12 with 'Mesh' magic) Xbox360 -> PC converter (full parse + re-serialise).

Section layout (both platforms, verified by byte-exact re-serialisation of the Xbox and PC base sections,
see mesh_validate.py; offsets stored in the header are relative to H = 0x10):
  0x00  4 root pointers (internal relocs): ->H, ->texture id list, ->material id list, ->aux (render tree)
  H     header 0x84 B ('Mesh', flags, matOff, numIndices, sphere, boxMin, boxMax, radius, modelType,
        9 opaque u32, groupOff, meshInfoOff, boneMapOff, faceOff, u16 numGroups/numMeshes/numBones/pad)
        + 0x0C B (u32 -1/0, 0, 0) -> copied as u32 words up to the first region
  every region below starts at an offset aligned to 32 relative to H:
  boneMap   u32[numBones]                      (only when the Xbox/PC section had one before meshInfo)
  meshInfo  52 B x numMeshes: u32 a, f32 b (LOD dist?), numGroups, skinSize, skinOff, vdataOff, 0,0,0,
            vfOff, numVerts, baseIndex, numTris
  palettes  (PC only) u32[skinSize] per skinned batch = sorted unique weighted global bone indices
  per batch: vertex format {u64 hash, u16 n, u8 stride, u8 0, u32 0, elems[n] {u32 sem, u16 off, u8 type, u8 0}}
            then vertex data (numVerts * stride)       (a format shared by several batches is written once)
  faces     u16 triangle-list indices (relative to the batch vertex buffer), numIndices
  groups    64 B: vec4 centre (stored LITTLE endian on Xbox too), baseIndex, numTris, numVerts, i32 x5, -1.., 0
  lists     {u32 n, textureId[n]} {u32 n, materialId[n]}   (immediately after the groups)
  tail      render tree + skeleton (copied verbatim, u32-swapped except u16 pairs found by mesh_tr8.tail_u16)
Only roots and tail carry internal pointers; ids (type 5/10) live in the lists. No external relocs.

Xbox -> PC: BE->LE; vertex element types 2 float3, 3 float4, 4 D3DCOLOR, 1 float2 -> swap32;
 0x13 short2 -> swap16; 0x11 DEC3N -> 5 UBYTE4N (b0=z, b1=y, b2=x, b3=127; 10-bit -> byte LUT learnt from
 pairs); 0x12 weights -> 6 (bytes [1,2,3,0]); 8 skin indices -> 7 (bytes [1,2,3,0], global -> palette index).
 Xbox batches index global bones directly; PC batches carry a palette of <= 42 bones (168 VS constants).
 Batches with > 42 weighted bones are split (first-fit per triangle, group order kept, groups split
 per batch, vertices of a sub-batch kept in their original relative order).
"""
import struct, sys, os, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
from mesh_tr8 import Mesh, SEM, H, tail_u16
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')
MAXBONES = 42
MAXVERTS = 0xFFFF
TYPEMAP = {2: 2, 0x11: 5, 0x13: 0x13, 8: 7, 0x12: 6, 4: 4, 3: 3, 1: 1}
SEM_IDX, SEM_W = 0x5156D8D3, 0x48E691C0

_DECL = None
def pc_decl_hash(elems):
    """elems: [(sem, off, pctype)]. Known table from base pairs; unknown -> deterministic synthetic hash."""
    global _DECL
    if _DECL is None:
        p = os.path.join(W, 'pc_vdecl_hash.pkl')
        _DECL = pickle.load(open(p, 'rb')) if os.path.exists(p) else {}
    k = tuple(tuple(x) for x in elems)
    if k in _DECL: return _DECL[k], True
    return hashlib.md5(repr(k).encode()).digest()[:8], False

_DEC3N_LUT = None
def dec3n_lut():
    """10-bit two's complement -> PC byte. Learnt from 8.2M base-pair components (work/render/dec3n_lut.pkl);
    fallback formula trunc(127.5 + s/4) (89% agreement)."""
    global _DEC3N_LUT
    if _DEC3N_LUT is None:
        p = os.path.join(W, 'dec3n_lut.pkl')
        if os.path.exists(p): _DEC3N_LUT = pickle.load(open(p, 'rb'))
        else:
            _DEC3N_LUT = [max(0, min(255, int(127.5 + ((v - 1024 if v >= 512 else v) / 4.0)))) for v in range(1024)]
    return _DEC3N_LUT

a32 = lambda x: (x + 31) & ~31   # alignment relative to H (H = 0x10 is itself 16-aligned)
def alignH(o): return H + a32(o - H)

# ------------------------------------------------------------------------------------------------ parse
def parse(d, endian, reloc_blob):
    """Parse a Mesh section into a platform-neutral model dict (raw byte blocks keep source endianness)."""
    e = '>' if endian in ('be', '>') else '<'
    m = Mesh(d, endian)
    rel = R.parse(reloc_blob, endian)
    M = dict(e=e, m=m, rel=rel, d=d)
    if m.numMeshes == 0 or m.meshInfoOff == 0xFFFFFFFF:
        M['empty'] = True
        return M
    M['empty'] = False
    starts = [H + m.meshInfoOff] + ([H + m.boneMapOff] if m.numBones and m.boneMapOff < m.meshInfoOff else [])
    M['hdr_end'] = min(starts)
    M['bonemap'] = d[H + m.boneMapOff:H + m.boneMapOff + 4 * m.numBones] if (m.numBones and m.boneMapOff < m.meshInfoOff) else None
    vf_seen = {}
    B = []
    for i, b in enumerate(m.meshes):
        vf = b['vf']
        nb = dict(raw=list(b['raw']), vf=vf, numVerts=b['numVerts'], baseIndex=b['baseIndex'], numTris=b['numTris'],
                  numGroups=b['numGroups'], skinSize=b['skinSize'], skinOff=b['skinOff'])
        nb['vf_shared_with'] = vf_seen.get(b['vfOff']) if vf else None
        if vf and b['vfOff'] not in vf_seen: vf_seen[b['vfOff']] = i
        nb['vdata'] = d[H + b['vdataOff']:H + b['vdataOff'] + b['numVerts'] * vf['stride']] if vf else b''
        nb['palette'] = (list(struct.unpack_from(e + '%dI' % b['skinSize'], d, H + b['skinOff'])) if b['skinSize'] else None)
        B.append(nb)
    M['batches'] = B
    M['groups'] = [d[g['off']:g['off'] + 64] for g in m.groups]
    M['ginfo'] = m.groups
    M['indices'] = list(m.indices())
    M['lists'] = (H + m.matOff, m.listsEnd)
    M['tail'] = m.listsEnd
    return M

# ------------------------------------------------------------------------------------------------ helpers
def _sw32_block(src, endian_in, endian_out):
    if endian_in == endian_out: return bytearray(src)
    out = bytearray(len(src))
    for o in range(0, len(src) - 3, 4): out[o:o + 4] = src[o:o + 4][::-1]
    out[len(src) & ~3:] = src[len(src) & ~3:]
    return out

def _elems(vf):
    return {s: (o, t) for s, o, t, _ in vf['elems']}

def batch_bones(M, b):
    """sorted unique bone indices with non-zero weight used by batch b (Xbox global indices)."""
    if not b['vf']: return None
    el = _elems(b['vf'])
    if SEM_IDX not in el: return None
    st = b['vf']['stride']; vd = b['vdata']; io = el[SEM_IDX][0]
    used = set()
    wo = el[SEM_W][0] if SEM_W in el else None
    for v in range(b['numVerts']):
        idx = vd[v * st + io:v * st + io + 4]
        if wo is not None:
            w = vd[v * st + wo:v * st + wo + 4]
            used.update(i for i, ww in zip(idx, w) if ww)
        else:
            used.update(idx)
    return sorted(used)

def vert_bones(b, v):
    el = _elems(b['vf']); st = b['vf']['stride']; vd = b['vdata']
    io = el[SEM_IDX][0]; idx = vd[v * st + io:v * st + io + 4]
    if SEM_W in el:
        wo = el[SEM_W][0]; w = vd[v * st + wo:v * st + wo + 4]
        return {i for i, ww in zip(idx, w) if ww}
    return set(idx)

# ------------------------------------------------------------------------------------------------ rebatch
def rebatch(M, maxbones=MAXBONES):
    """Split skinned Xbox batches using > maxbones weighted bones. Works on the Xbox-endian model; returns
    a new list of (batch, [group pieces]) where each group piece = (src group index, [triangles])."""
    m = M['m']; idx = M['indices']; out = []
    gi = 0
    for b in M['batches']:
        groups = list(range(gi, gi + b['numGroups'])); gi += b['numGroups']
        bones = batch_bones(M, b)
        if bones is None or len(bones) <= maxbones:
            out.append((b, None, groups)); continue
        vb = [vert_bones(b, v) for v in range(b['numVerts'])]
        subs = []   # each: dict(bones=set, verts=set, pieces={group: [tris]})
        for g in groups:
            G = M['ginfo'][g]
            for t in range(G['numTris']):
                tri = idx[G['baseIndex'] + 3 * t:G['baseIndex'] + 3 * t + 3]
                tb = vb[tri[0]] | vb[tri[1]] | vb[tri[2]]
                for s in subs:
                    nb = s['bones'] | tb
                    if len(nb) <= maxbones and len(s['verts'] | set(tri)) <= MAXVERTS:
                        break
                else:
                    s = dict(bones=set(), verts=set(), pieces={}); subs.append(s)
                s['bones'] |= tb; s['verts'].update(tri)
                s['pieces'].setdefault(g, []).append(tri)
        for s in subs:
            out.append((b, s, [g for g in groups if g in s['pieces']]))
    return out

# ------------------------------------------------------------------------------------------------ vertex conversion
def convert_vertices(b, vmap, palette):
    """Xbox batch b -> PC vertex bytes for Xbox vertex indices vmap (list). palette: list of global bones or None."""
    vf = b['vf']; st = vf['stride']; vd = b['vdata']
    L = dec3n_lut()
    lut = {g: i for i, g in enumerate(palette)} if palette else {}
    out = bytearray(st * len(vmap))
    ops = []
    covered = bytearray(st)
    for s, eo, t, _ in vf['elems']:
        ops.append((eo, t))
        n = {2: 12, 3: 16, 1: 8}.get(t, 4)
        for k in range(eo, min(st, eo + n)): covered[k] = 1
    for j, v in enumerate(vmap):
        src = vd[v * st:(v + 1) * st]; o = j * st
        # default: swap32 words (covers padding too)
        for k in range(0, st - 3, 4): out[o + k:o + k + 4] = src[k:k + 4][::-1]
        for eo, t in ops:
            a = o + eo
            if t == 0x13:
                out[a:a + 4] = bytes((src[eo + 1], src[eo], src[eo + 3], src[eo + 2]))
            elif t == 0x11:
                x = (src[eo] << 24) | (src[eo + 1] << 16) | (src[eo + 2] << 8) | src[eo + 3]
                out[a:a + 4] = bytes((L[(x >> 20) & 0x3ff], L[(x >> 10) & 0x3ff], L[x & 0x3ff], 127))
            elif t == 0x12:
                out[a:a + 4] = bytes((src[eo + 1], src[eo + 2], src[eo + 3], src[eo]))
            elif t == 8:
                out[a:a + 4] = bytes(lut.get(i, 0) for i in (src[eo + 1], src[eo + 2], src[eo + 3], src[eo]))
    return out

def convert_vdecl(vf, xd):
    """Xbox vertex format block -> PC block bytes."""
    n = vf['n']
    pel = [(s, eo, TYPEMAP.get(t, t)) for s, eo, t, _ in vf['elems']]
    h, known = pc_decl_hash(pel)
    blk = bytearray(16 + 8 * n)
    blk[0:8] = h
    o = vf['off']
    struct.pack_into('<HBB', blk, 8, n, xd[o + 10], xd[o + 11])
    blk[12:16] = xd[o + 12:o + 16][::-1]
    for j, (s, eo, t, p) in enumerate(vf['elems']):
        struct.pack_into('<IHBB', blk, 16 + 8 * j, s, eo, TYPEMAP.get(t, t), p)
    return bytes(blk), known

# ------------------------------------------------------------------------------------------------ convert
def convert(xd, xreloc, ids=None, info=None, do_rebatch=True):
    """Convert one Xbox Mesh section. ids(type, xid)->pcid optional. Returns (pc_data, pc_reloc_blob).
    info (dict) receives: 'shift' (old offset -> new offset for offsets in verbatim regions: header, lists, tail;
    use it for external relocs of OTHER sections that point into this mesh: verified on base pairs, all 1026 such
    relocs come from DTPData (type 7) sections and target the tail (skeleton); PC keeps the tail-relative offset
    in 1026/1026), 'shift_params' {hdr_end, lists_start, delta} (picklable: o<hdr_end -> o; o>=lists_start -> o+delta),
    'rebatched',
    'unknown_decls', 'palettes', 'max_palette'."""
    if info is None: info = {}
    M = parse(xd, 'be', xreloc)
    rel = M['rel']; m = M['m']
    u16w = tail_u16(xd, 'be', rel, m)
    if M['empty']:
        return _convert_inplace_empty(xd, rel, m, u16w, ids, info)
    plan = rebatch(M) if do_rebatch else [(b, None, list(range(sum(x['numGroups'] for x in M['batches'][:i]), sum(x['numGroups'] for x in M['batches'][:i + 1])))) for i, b in enumerate(M['batches'])]
    info['rebatched'] = len(plan) != len(M['batches'])
    info['unknown_decls'] = 0
    xidx = M['indices']
    # ---- build PC batches: (src batch, vmap, palette, group pieces [(src g, tri list in new local idx)])
    PB = []
    for b, sub, groups in plan:
        if sub is None:
            vmap = list(range(b['numVerts']))
            pieces = []
            for g in groups:
                G = M['ginfo'][g]
                pieces.append((g, [tuple(xidx[G['baseIndex'] + 3 * t:G['baseIndex'] + 3 * t + 3]) for t in range(G['numTris'])]))
            bones = batch_bones(M, b)
        else:
            vmap = sorted(sub['verts'])
            loc = {v: i for i, v in enumerate(vmap)}
            pieces = [(g, [tuple(loc[v] for v in tri) for tri in sub['pieces'][g]]) for g in groups]
            bones = sorted(sub['bones'])
        PB.append(dict(src=b, vmap=vmap, palette=bones, pieces=pieces, whole=sub is None))
    info['palettes'] = [p['palette'] for p in PB]
    info['max_palette'] = max([len(p['palette']) for p in PB if p['palette']] or [0])
    # ---- layout
    out = bytearray()
    # roots + header (+ gap words) copied with swap32, u16 fields fixed later
    hdr_end = M['hdr_end']
    out += _sw32_block(xd[0:hdr_end], 'be', 'le')
    out[H + 0x7C:H + 0x84] = b''.join(xd[H + 0x7C + 2 * k:H + 0x7E + 2 * k][::-1] for k in range(4))
    def pad(): out.extend(bytes(alignH(len(out)) - len(out)))
    if M['bonemap'] is not None:
        pad(); bm_off = len(out); out += _sw32_block(M['bonemap'], 'be', 'le')
    else: bm_off = None
    pad(); mi_off = len(out); out += bytes(52 * len(PB))
    pal_off = []
    for p in PB:
        if p['palette'] is not None:
            pad(); pal_off.append(len(out)); out += struct.pack('<%dI' % len(p['palette']), *p['palette'])
        else: pal_off.append(None)
    vf_off = []; vd_off = []; vf_written = {}
    for p in PB:
        b = p['src']; vf = b['vf']
        if vf is None: vf_off.append(None); vd_off.append(None); continue
        key = vf['off']
        if key in vf_written and p['whole']:
            vf_off.append(vf_written[key])
        else:
            pad(); vf_off.append(len(out))
            blk, known = convert_vdecl(vf, xd); info['unknown_decls'] += not known
            out += blk; vf_written.setdefault(key, vf_off[-1])
        pad(); vd_off.append(len(out))
        out += convert_vertices(b, p['vmap'], p['palette'])
    pad(); face_off = len(out)
    nidx = 0; grecs = []
    for bi, p in enumerate(PB):
        p['base'] = nidx; ntri = 0
        for g, tris in p['pieces']:
            gb = nidx
            for tri in tris: out += struct.pack('<3H', *tri)
            nidx += 3 * len(tris); ntri += len(tris)
            grecs.append((g, gb, tris, p))
        p['ntri'] = ntri
    assert nidx == m.numIndices, (nidx, m.numIndices)
    pad(); grp_off = len(out)
    for g, gb, tris, p in grecs:
        src = M['groups'][g]
        rec = bytearray(_sw32_block(src, 'be', 'le')); rec[0:16] = src[0:16]
        nv = len(set(v for t in tris for v in t))
        struct.pack_into('<III', rec, 16, gb, len(tris), nv if not p['whole'] else M['ginfo'][g]['numVerts'])
        out += rec
    # lists + tail verbatim (moved by a constant delta)
    lstart, lend = M['lists']
    delta = len(out) - lstart
    assert delta % 16 == 0
    out += _sw32_block(xd[lstart:], 'be', 'le')
    for o in u16w:
        out[o + delta:o + delta + 4] = bytes((xd[o + 1], xd[o], xd[o + 3], xd[o + 2]))
    # ---- header fields
    struct.pack_into('<I', out, H + 0x08, m.matOff + delta)
    struct.pack_into('<IIII', out, H + 0x6C, grp_off - H, mi_off - H, (bm_off - H) if bm_off is not None else m.boneMapOff, face_off - H)
    struct.pack_into('<HH', out, H + 0x7C, len(grecs), len(PB))
    # ---- mesh infos
    for bi, p in enumerate(PB):
        r = list(p['src']['raw'])
        r[2] = len(p['pieces'])
        r[3] = len(p['palette']) if p['palette'] is not None else 0
        r[4] = (pal_off[bi] - H) if pal_off[bi] is not None else 0xFFFFFFFF
        r[5] = (vd_off[bi] - H) if vd_off[bi] is not None else r[5]
        r[9] = (vf_off[bi] - H) if vf_off[bi] is not None else r[9]
        r[10] = len(p['vmap']); r[11] = p['base']; r[12] = p['ntri']
        struct.pack_into('<IfIIIIIIIIIII', out, mi_off + 52 * bi, *r)
    # ---- relocations: sources in roots/tail, targets in hdr/lists/tail
    def sh(o):
        if o >= lstart: return o + delta
        if o < hdr_end: return o
        raise ValueError('pointer into rebuilt region 0x%x' % o)
    info['shift'] = sh
    info['shift_params'] = dict(hdr_end=hdr_end, lists_start=lstart, delta=delta)   # picklable form of shift()
    rel.internal = [(sh(a), sh(t)) for a, t in rel.internal]
    assert not rel.external, 'unexpected external relocs in mesh'
    rel.idref = [(t, sh(o)) for t, o in rel.idref]
    rel.idref_a = [(t, sh(o)) for t, o in rel.idref_a]
    if ids is not None:
        for t, o in rel.idref + rel.idref_a:
            xid = struct.unpack_from('<I', out, o)[0]
            struct.pack_into('<I', out, o, ids(t, xid))
    return bytes(out), R.write(rel, 'le')

def _convert_inplace_empty(xd, rel, m, u16w, ids, info):
    """Meshes without batches (numMeshes 0): same size, swap32 + u16 fixes."""
    out = _sw32_block(xd, 'be', 'le')
    out[H + 0x7C:H + 0x84] = b''.join(xd[H + 0x7C + 2 * k:H + 0x7E + 2 * k][::-1] for k in range(4))
    for o in u16w: out[o:o + 4] = bytes((xd[o + 1], xd[o], xd[o + 3], xd[o + 2]))
    info.update(shift=lambda o: o, shift_params=dict(hdr_end=len(xd), lists_start=0, delta=0), rebatched=False, unknown_decls=0, palettes=[], max_palette=0)
    if ids is not None:
        for t, o in rel.idref + rel.idref_a:
            struct.pack_into('<I', out, o, ids(t, struct.unpack_from('>I', xd, o)[0]))
    return bytes(out), R.write(rel, 'le')
