"""TR8 (Tomb Raider Underworld) Mesh section (type 12) parser, both endians.
Layout (all offsets in the Mesh header are relative to the header itself, H = 0x10 in the section):
 section+0x00: 4 root pointers (relocated): ->H, ->matTable+0, ->matTable+4, ->aux
 H+0x00 'Mesh' magic (u32 0x4D657368), +4 flags/version u32, +8 matTable off, +0xC numIndices,
 +0x10 vec4 sphere centre, +0x20 vec4 boxMin, +0x30 vec4 boxMax, +0x40 f32 radius, +0x44 u32 modelType,
 +0x48..0x6C opaque 9 u32, +0x6C groupOff, +0x70 meshInfoOff, +0x74 boneMapOff, +0x78 faceDataOff,
 +0x7C u16 numGroups, u16 numMeshes(batches), u16 numBones, u16 pad
 MeshInfo (52 B, at H+meshInfoOff): u32 0, f32 FLT_MAX, u32 numGroups, u32 skinMapSize, u32 skinMapOff,
    u32 vertexDataOff, u32 0,0,0, u32 vertexFormatOff, u32 numVerts, u32 baseIndex, u32 numTris
 VertexFormat (at H+vfOff): u64 hash, u16 numElems, u8 stride, u8 pad, u32 0; elems[n] {u32 semanticHash, u16 offset, u8 type, u8 pad}
 Group (64 B, at H+groupOff): vec4 centre (LITTLE-endian even on Xbox), u32 baseIndex, numTris, numVerts, 0, 0, drawGroup?, materialIndex, -1 x4, 0
 Index buffer: u16 at H+faceDataOff, numIndices.
 MatTable (at H+matOff): {u32 n, textureId[n]} then {u32 n, materialId[n]} (root ptrs 1/2 point at them)
"""
import struct
SEM = {0xD2F7D823: 'POSITION', 0x36F5E414: 'NORMAL', 0xF1ED11C3: 'TANGENT', 0x64A86F01: 'BINORMAL', 0x48E691C0: 'SKINWEIGHTS',
       0x5156D8D3: 'SKININDICES', 0x8317902A: 'TEXCOORD1', 0x8E54B6F3: 'TEXCOORD2', 0x8A95AB44: 'TEXCOORD3', 0x7E7DD623: 'COLOR1', 0x733EF0FA: 'COLOR2'}
H = 0x10

class Mesh:
    def __init__(self, d, endian):
        self.d, self.e = d, ('>' if endian in ('be', '>') else '<')
        e = self.e
        u = lambda o, f='I': struct.unpack_from(e + f, d, H + o)[0]
        self.u = u
        self.magic = d[H:H + 4]
        assert self.magic in (b'hseM', b'Mesh'), self.magic
        self.flags, self.matOff, self.numIndices = u(4), u(8), u(0xC)
        self.modelType = u(0x44)
        self.groupOff, self.meshInfoOff, self.boneMapOff, self.faceOff = u(0x6C), u(0x70), u(0x74), u(0x78)
        self.numGroups, self.numMeshes, self.numBones = u(0x7C, 'H'), u(0x7E, 'H'), u(0x80, 'H')
        self.meshes = []
        for i in range(self.numMeshes):
            r = struct.unpack_from(e + 'IfIIIIIIIIIII', d, H + self.meshInfoOff + 52 * i)
            m = dict(off=H + self.meshInfoOff + 52 * i, numGroups=r[2], skinSize=r[3], skinOff=r[4], vdataOff=r[5], vfOff=r[9], numVerts=r[10], baseIndex=r[11], numTris=r[12], raw=r)
            m['vf'] = self.vertex_format(m['vfOff']) if m['vfOff'] not in (0, 0xffffffff) else None
            self.meshes.append(m)
        self.groups = []
        for i in range(self.numGroups):
            o = H + self.groupOff + 64 * i
            r = struct.unpack_from(e + '12i', d, o + 16)
            self.groups.append(dict(off=o, center=struct.unpack_from('<4f', d, o), baseIndex=r[0], numTris=r[1], numVerts=r[2], x0=r[3], x1=r[4], drawGroup=r[5], material=r[6], tail=r[7:]))
        o = H + self.matOff   # texture id list {n, ids[n]} immediately followed by material id list {n, ids[n]}
        nt = struct.unpack_from(e + 'I', d, o)[0]
        self.textures = list(struct.unpack_from(e + '%dI' % nt, d, o + 4)); o += 4 + 4 * nt
        nm = struct.unpack_from(e + 'I', d, o)[0]
        self.materials = list(struct.unpack_from(e + '%dI' % nm, d, o + 4)); self.listsEnd = o + 4 + 4 * nm
    def vertex_format(self, off):
        e, d = self.e, self.d
        o = H + off
        h64 = d[o:o + 8]
        n, stride = struct.unpack_from(e + 'HB', d, o + 8)
        elems = []
        for k in range(n):
            sem, eo, typ, pad = struct.unpack_from(e + 'IHBB', d, o + 16 + 8 * k)
            elems.append((sem, eo, typ, pad))
        return dict(off=o, hash=h64, n=n, stride=stride, elems=elems)
    def indices(self):
        return struct.unpack_from(self.e + '%dH' % self.numIndices, self.d, H + self.faceOff)

def tail_u16(d, endian, rel, m):
    """Offsets (absolute, in section data) of 32-bit words in the mesh tail that hold TWO u16 values
    (need a 16-bit swap instead of a 32-bit swap). Walks the pointer graph:
      aux (root ptr @0x0C): {ptr topArray, u16 nTop, u16}
      top record (0x14): {ptr nodes, ptr edges, u32, u16 nNodes, u16 nEdges, u16, u16}
      node (0x30): {vec4, ptr list, u16 nList, u16, ptr shape, u16 x2, u16 x2, u32 x3}
      list entry (0x20): {vec4, f32, u16 x2, u32 x2};  edge (8): {f32, u16, u16};  shape: {u32 n, 3 u32, vec4[n]}
      skeleton: {u32 n, ptr records} records 0x40 with {i16 firstVert, i16 lastVert} at +0x34
    """
    e = '>' if endian in ('be', '>') else '<'
    ptr = dict(rel.internal)
    u32 = lambda o: struct.unpack_from(e + 'I', d, o)[0]
    u16 = lambda o: struct.unpack_from(e + 'H', d, o)[0]
    N = len(d); out = set()
    aux = ptr.get(0x0C)
    if aux is not None and aux + 8 <= N:
        top = ptr.get(aux)
        out.add(aux + 4)
        if top is not None:
            nTop = u16(aux + 4)
            for i in range(nTop):
                r = top + 0x14 * i
                if r + 0x14 > N: break
                out.add(r + 0x0C); out.add(r + 0x10)
                nodes = ptr.get(r); edges = ptr.get(r + 4)
                nn, ne = u16(r + 0x0C), u16(r + 0x0E)
                if nodes is not None:
                    for k in range(nn):
                        n = nodes + 0x30 * k
                        if n + 0x30 > N: break
                        out.update((n + 0x14, n + 0x1C, n + 0x20))
                        lst = ptr.get(n + 0x10)
                        if lst is not None:
                            for j in range(u16(n + 0x14)):
                                if lst + 0x20 * j + 0x18 <= N: out.add(lst + 0x20 * j + 0x14)
                if edges is not None:
                    for k in range(ne):
                        if edges + 8 * k + 8 <= N: out.add(edges + 8 * k + 4)
    # skeleton: pointer s whose word before holds the record count and target = array of 0x40 records
    for s, t in ptr.items():
        if s < m.listsEnd or s < 4: continue
        n = u32(s - 4)
        if 0 < n <= 4096 and t > s and t + 0x40 * n <= N and (t - s) in (4, 0xC):
            for k in range(n): out.add(t + 0x40 * k + 0x34)
    return sorted(o for o in out if o >= m.listsEnd and o + 4 <= N)
