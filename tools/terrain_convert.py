"""TR8 terrain / level render data (type-12 sections WITHOUT the 'Mesh' magic) Xbox360 -> PC converter.

Layout (verified on base pairs; H = u32 at section+0, offsets below are relative to H unless noted):
 sec+0x00 u32 H, +0x04 ptr->H, +0x08 ptr->texture id list {u32 n, u32 ids[n]}, +0x0C ptr->material id list {u32 n, ids}
 H+0x00 vec4, H+0x10 vec4 (bounds)
 H+0x20 offA,nA (32B "cell" records: 7 x u32/f32, then {u16, u8, u8})
 H+0x28 offY,nY (always 0x60; 32B records: u32,u32, u32 'hash' (looks like a raw LE heap pointer of the build tool;
       base pairs mapped by learnt table, unknown copied raw; DLC has 0xCCCCCCCC in 68%), u16,u8,u8, i32 x4)
 H+0x30 offVF,nVF, H+0x38 sizeVF (vertex formats: u64 hash (same on both platforms), u16 n, u8 stride, u8, u32 0,
                                   n x {u32 semantic, u16 offset, u8 type, u8 pad})
 H+0x3C offVB,nVB (16B: u32 vdataOff, u32 0, u32 nVerts, u32 vfIndex)
 H+0x44 offZ: u32 table[nA] (one slot per A/BVH node, H-relative offset of a draw list or 0), padded to 32,
       then draw lists (32B aligned): {u16 n, u16 seq; n x {u16 yIndex, u16 indexCount, u32 indexStart}}
       Y record = draw batch/material: {u32 idx, u32 vbIndex, u32 platform hash, u16, u8, u8, i32 x4}
       (verified: every entry's index range lies in the index buffer and indexes < numVerts of Y[yIndex].vb)
 H+0x4C u32, H+0x50 offIdx,nIdx (u16 index buffer)
 vertex element types seen: 2 float3, 0x0A 4 x s16, 0x13 2 x s16, 0x04 D3DCOLOR (u32)
"""
import struct, sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')
_YHASH = None
def yhash_map():
    global _YHASH
    if _YHASH is None:
        p = os.path.join(W, 'terrain_yhash.pkl')
        _YHASH = pickle.load(open(p, 'rb')) if os.path.exists(p) else {}
    return _YHASH

def is_terrain(d):
    return len(d) >= 0x20 and d[0x10:0x14] not in (b'hseM', b'Mesh')

def parse(d, e='>'):
    u = lambda o: struct.unpack_from(e + 'I', d, o)[0]
    H = u(0)
    f = struct.unpack_from(e + '14I', d, H + 0x20)
    T = dict(H=H, offA=f[0], nA=f[1], offY=f[2], nY=f[3], offVF=f[4], nVF=f[5], sizeVF=f[6], offVB=f[7], nVB=f[8],
             offZ=f[9], nZ=f[10], w=f[11], offIdx=f[12], nIdx=f[13])
    vfs = []; o = H + T['offVF']
    for k in range(T['nVF']):
        n, stride = struct.unpack_from(e + 'HB', d, o + 8)
        el = [struct.unpack_from(e + 'IHBB', d, o + 16 + 8 * j) for j in range(n)]
        vfs.append(dict(off=o, n=n, stride=stride, elems=el)); o += 16 + 8 * n
    T['vfs'] = vfs
    T['vbs'] = [struct.unpack_from(e + '4I', d, H + T['offVB'] + 16 * k) for k in range(T['nVB'])]
    T['Y'] = [struct.unpack_from(e + '3IHBB4i', d, H + T['offY'] + 32 * k) for k in range(T['nY'])]
    return T

def draw_lists(d, T, e='>'):
    """[(slot, seq, [(yIndex, indexCount, indexStart)])] from the Z region."""
    H = T['H']; z0 = H + T['offZ']; out = []
    for k in range(T['nA']):
        t = struct.unpack_from(e + 'I', d, z0 + 4 * k)[0]
        if not t: continue
        L = H + t; n, seq = struct.unpack_from(e + 'HH', d, L)
        out.append((k, seq, [struct.unpack_from(e + 'HHI', d, L + 4 + 8 * j) for j in range(n)]))
    return out

def convert(xd, xreloc, ids=None, stats=None):
    """ids(type, xid) -> pc id (optional). Returns (pc_data, pc_reloc)."""
    rel = R.parse(xreloc, 'be')
    T = parse(xd, '>'); H = T['H']
    out = bytearray(len(xd))
    for o in range(0, len(xd) - 3, 4): out[o:o + 4] = xd[o:o + 4][::-1]
    def s16(o, n):
        for k in range(n): out[o + 2 * k:o + 2 * k + 2] = xd[o + 2 * k:o + 2 * k + 2][::-1]
    def cp(o, n): out[o:o + n] = xd[o:o + n]
    ym = yhash_map()
    for k in range(T['nY']):
        r = H + T['offY'] + 32 * k
        xh = xd[r + 8:r + 12]
        ph = ym.get(bytes(xh))
        if ph is not None: out[r + 8:r + 12] = ph
        else:
            # the field looks like a build-tool heap pointer written raw (LE) on both platforms (DLC: mostly
            # 0xCCCCCCCC = MSVC uninitialised fill) -> runtime-overwritten/unused; copy the raw bytes
            out[r + 8:r + 12] = xh
            if stats is not None: stats['yhash_unknown'] = stats.get('yhash_unknown', 0) + 1
        s16(r + 12, 1); cp(r + 14, 2)   # {u16, u8, u8}
    s16(H + T['offIdx'], T['nIdx'] + (T['nIdx'] & 1))  # odd count: pad u16 too
    for k in range(T['nA']):
        r = H + T['offA'] + 32 * k
        s16(r + 28, 1); cp(r + 30, 2)
    # Z: offset table then batch records up to the vertex formats
    z0 = H + T['offZ']; zend = H + T['offVF']
    o = z0; first = zend; lists = set()
    while o < first and o + 4 <= zend:
        v = struct.unpack_from('>I', xd, o)[0]
        if v and z0 <= H + v < zend:
            lists.add(H + v); first = min(first, H + v)
        o += 4
    for L in sorted(lists):   # batch list: u16 n, u16 id, then n x {u16, u16, u32}; first entry overlaps header+4
        n = struct.unpack_from('>H', xd, L)[0]
        s16(L, 2)
        for k in range(n):
            e = L + 4 + 8 * k
            if e + 8 > zend: break
            s16(e, 2)
    for vf in T['vfs']:
        o = vf['off']; cp(o, 8); s16(o + 8, 1); cp(o + 10, 2)
        for j in range(vf['n']): s16(o + 16 + 8 * j + 4, 1); cp(o + 16 + 8 * j + 6, 2)
    for voff, _z, nv, vfi in T['vbs']:
        vf = T['vfs'][vfi] if vfi < len(T['vfs']) else None
        if vf is None: continue
        base = H + voff; st = vf['stride']
        for sem, eo, typ, _p in vf['elems']:
            for v in range(nv):
                a = base + v * st + eo
                if typ in (0x0A,): s16(a, 4)
                elif typ in (0x13,): s16(a, 2)
                elif typ in (1, 2, 4): pass  # float2 / float3 / D3DCOLOR: already swapped as u32
                elif stats is not None: stats['vtype_%x' % typ] = stats.get('vtype_%x' % typ, 0) + 1
    if ids is not None:
        for t, off in rel.idref + rel.idref_a:
            xid = struct.unpack_from('>I', xd, off)[0]
            struct.pack_into('<I', out, off, ids(t, xid))
    return bytes(out), R.write(rel, 'le')
