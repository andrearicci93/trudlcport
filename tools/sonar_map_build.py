r"""Sonar maps for units that only have the "MAP" placeholder (Q6, owner's wish, NOT Xbox-faithful): the unit's
collision geometry (TerrainGroup meshes) as the *_map.drm collision mesh (old plan A11; workspace docs
Befund-Sonar-DLC2-1411.md "Fix-Vorschlag 3", Befund-Q6-Sonar-DLC2-1711.md).

Formats (read from the data):
  map DRM = 2 type-13 sections: [0] map header (portals, floor byte - kept byte-identical), [1] one collision Mesh
  (tools/map_mesh_fix.py): header 0x58 B {+0x00 bbox min vec4, +0x10 bbox max vec4, +0x20 position vec4 (maps: 0),
  +0x30 -> vertices (float4), +0x34 -> faces (20 B), +0x38 -> KD nodes (16 B), +0x3c s32, +0x40 node count, +0x44 face
  count, +0x48 vertex count, +0x4c / +0x50 s32, +0x54 {u16 vertexType 1, u16 height}}; the collision Mesh of a unit
  TerrainGroup is the same struct (0x60 B, +0x3c -> its group, +0x20 = the group offset: world = local + position,
  tools/collision_faces.py).
  KD node {f32 a, f32 b, u32 index, u8 axis, u8 leaf face count, 2 bytes}: leaf (count > 0) = faces index ..
  index + count - 1; inner = children k + 1 and k + index - which float bounds which child is decided by `bih` on
  real maps (not assumed).

Modes (from the repository root; read-only except build / batch, which write only OUT):
  ../bin/pyt -t 1800 tools/sonar_map_build.py frame UNIT MAP
        UNIT / MAP = a file or pc:name.drm (the player's PC archives): collision meshes (world) vs the map mesh:
        bounding boxes, vertex / face counts, share of map vertices within 25 / 100 / 400 units of a collision face,
        face byte statistics of both - the frame proof for the conversion (translation 0 expected)
  ../bin/pyt -t 1800 tools/sonar_map_build.py bih MAP [MAP ...]
        the KD node semantics on real maps: per inner node the left / right subtree face extents along the axis
        against the two floats; leaf sizes, depth, header words +0x3c / +0x4c / +0x50 / +0x54
  ../bin/pyt -t 1800 tools/sonar_map_build.py build UNIT MAP_IN OUT_MAP
        the placeholder MAP_IN with its mesh section replaced by the unit's collision geometry (world coordinates,
        faces as in the unit, KD tree built with the rule `bih` proved); header section byte-identical; then `check`
  ../bin/pyt -t 1800 tools/sonar_map_build.py check MAP [MAP ...]
        gate on a built map: mesh found, counts, vertex count <= 65535 (u16 reveal entry), every face index in range,
        KD tree: every face in exactly one leaf, every node inside the array, leaf size <= 255, both floats bound
        their child as `bih` found it, bbox = the vertices' bbox, header section = the input's
  ../bin/pyt -t 3600 tools/sonar_map_build.py batch UNIT_DIR MAP_DIR OUT_DIR [--report R.json] name ...
        build + check for every unit name (UNIT_DIR/name.drm + MAP_DIR/name_map.drm -> OUT_DIR/name_map.drm)
  Read-only helpers: bits MAP.. (face byte 0 rebuilt from the geometry vs real maps, header word candidates);
  portals MAP.. (each portal point of the map header against the map's own mesh); big UNIT [N] (largest collision
  faces); hdr MAP.. (sections, relocations, header words); pic MAP OUT.png [SIZE] (top view, writes only OUT.png)

Proofs (2026-11-17, real maps dlc_yggdrasil_hall01 / dlc_caverns / l7_yggdrasil / placeholder): frame = collision +
Level+0x80; inner node a >= max(child k+1), b <= min(child k+index) on every inner node; +0x54 = {1, depth + 1};
+0x4c = zero-area faces; face edge bits as face_flags (vertex bits only approximated: a superset of the real ones).
Saves: the reveal entry of a map keeps the vertex count it was saved with and the exe does not compare it with a
replaced map (docs/ENGINE.md "PDA sonar map mesh, proved on real maps") - test new maps with a new game.
"""
import sys, os, struct, json, math, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
import map_mesh_fix as M

BS = chr(92)
LEAF_MAX = 2            # faces per leaf when building (real maps, `bih`: leaves of 1-2 faces are 82-88 %, up to 8)
VERT_MAX = 65535        # reveal entry vertex count is a u16 (Befund-TruXenia-Sonar-1411: entry +0xc u16)


class Sec:
    def __init__(self, t, i, data, reloc):
        self.type, self.id, self.data, self.reloc = t, i, bytes(data) if data is not None else None, bytes(reloc or b'')


def load(src):
    """[Sec] of a DRM file or pc:name.drm (PC patch.000 / bigfile.000)"""
    if src.startswith('pc:'):
        import dtp_word_classes as C
        S = C.find(C.PC, 'le', 'pc-w' + BS + src[3:])
        if S is None: sys.exit('%s not in the PC archives' % src)
        return [Sec(s['type'], s['id'], s['data'], s['reloc']) for s in S]
    D = DW.read(open(src, 'rb').read(), 'le')
    return [Sec(s.type, s.id, s.data, s.reloc) for s in D.sections]


def rels(S):
    out = []
    for s in S:
        r = R.parse(s.reloc, 'le')
        out.append((dict(r.internal), {so: (si, do) for si, so, do in r.external}))
    return out


def tgt(RL, si, o):
    itn, ext = RL[si]
    if o in itn: return si, itn[o]
    if o in ext: return ext[o]
    return None


def collision(S):
    """unit collision in world coordinates: (vertices [(x, y, z)], faces [(i0, i1, i2, flags u32, b10)], per-mesh rows)
    - TerrainGroup layout as tools/collision_faces.meshes"""
    RL = rels(S)
    t = tgt(RL, 0, 0)
    if t is None: return [], [], []
    ti, to = t; td = S[ti].data
    ntg = struct.unpack_from('<i', td, to + 8)[0]
    groups = []
    g = tgt(RL, ti, to + 0xc)
    if g is not None: groups += [(g[0], g[1] + 0x50 * k) for k in range(ntg)]
    g2 = tgt(RL, ti, to + 0x10)
    if g2 is not None and g2 not in groups: groups.append(g2)
    V, F, rows, seen = [], [], [], set()
    for gs, go in groups:
        m = tgt(RL, gs, go + 0x38)
        if m is None or m in seen: continue
        seen.add(m); ms, mo = m; md = S[ms].data
        px, py, pz = struct.unpack_from('<3f', md, mo + 0x20)
        nn, nf, nv = struct.unpack_from('<3I', md, mo + 0x40)
        vs, vo = tgt(RL, ms, mo + 0x30); fs, fo = tgt(RL, ms, mo + 0x34)
        vd = S[vs].data; fd = S[fs].data + b'\0' * 4
        base = len(V)
        for k in range(nv):
            x, y, z = struct.unpack_from('<3f', vd, vo + 16 * k); V.append((x + px, y + py, z + pz))
        bad = 0
        for k in range(nf):
            i0, i1, i2, fl = struct.unpack_from('<4I', fd, fo + 20 * k)
            if max(i0, i1, i2) >= nv: bad += 1; continue
            F.append((i0 + base, i1 + base, i2 + base, fl, fd[fo + 20 * k + 16]))
        rows.append(dict(group_off=go, mesh=(ms, mo), pos=(px, py, pz), nodes=nn, faces=nf, verts=nv, bad_faces=bad,
                         w3c=struct.unpack_from('<I', md, mo + 0x3c)[0], w4c=struct.unpack_from('<I', md, mo + 0x4c)[0],
                         w50=struct.unpack_from('<I', md, mo + 0x50)[0], w54=struct.unpack_from('<2H', md, mo + 0x54)))
    return V, F, rows


def origin(S):
    """Level+0x80 (unit origin vector, docs/ENGINE.md 4.1 / 4.3: live position = data - Level+0x80 + P)"""
    return struct.unpack_from('<3f', S[0].data, 0x80)


def map_mesh(S):
    """(section index, mesh tuple of map_mesh_fix.find_mesh, vertices, faces raw 20 B, nodes raw) of a map DRM"""
    for k, s in enumerate(S):
        if s.type != 13 or not s.data: continue
        r = R.parse(s.reloc, 'le')
        m = M.find_mesh(s.data, r, 'le')
        if m is None: continue
        h, nn, nf, nv, vt, fs, (vo, fo, no) = m
        V = [struct.unpack_from('<3f', s.data, vo + 16 * j) for j in range(nv)]
        F = [s.data[fo + fs * j:fo + fs * j + fs] for j in range(nf)]
        N = [s.data[no + 16 * j:no + 16 * j + 16] for j in range(nn)]
        return k, m, V, F, N
    return None


def bbox(V):
    lo = [min(v[j] for v in V) for j in range(3)] if V else [0.0] * 3
    hi = [max(v[j] for v in V) for j in range(3)] if V else [0.0] * 3
    return lo, hi


def fmt(v): return '(%s)' % ', '.join('%.0f' % x for x in v)


# ------------------------------------------------------------------------------------------------ geometry
def pt_tri(p, a, b, c):
    """distance point - triangle (Ericson, Real-Time Collision Detection 5.1.5)"""
    sub = lambda u, w: (u[0] - w[0], u[1] - w[1], u[2] - w[2])
    dot = lambda u, w: u[0] * w[0] + u[1] * w[1] + u[2] * w[2]
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0: q = a
    else:
        bp = sub(p, b); d3, d4 = dot(ab, bp), dot(ac, bp)
        cp = sub(p, c); d5, d6 = dot(ab, cp), dot(ac, cp)
        vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
        if d3 >= 0 and d4 <= d3: q = b
        elif d6 >= 0 and d5 <= d6: q = c
        elif vc <= 0 and d1 >= 0 and d3 <= 0:
            v = d1 / (d1 - d3); q = (a[0] + v * ab[0], a[1] + v * ab[1], a[2] + v * ab[2])
        elif vb <= 0 and d2 >= 0 and d6 <= 0:
            w = d2 / (d2 - d6); q = (a[0] + w * ac[0], a[1] + w * ac[1], a[2] + w * ac[2])
        elif va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
            w = (d4 - d3) / ((d4 - d3) + (d5 - d6)); bc = sub(c, b)
            q = (b[0] + w * bc[0], b[1] + w * bc[1], b[2] + w * bc[2])
        else:
            den = 1.0 / (va + vb + vc); v = vb * den; w = vc * den
            q = (a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w)
    return math.sqrt(sum((p[j] - q[j]) ** 2 for j in range(3)))


class Grid:
    """triangles bucketed by their bounding box (cell CELL) for near-point queries"""
    def __init__(self, V, F, cell=400.0):
        self.V, self.F, self.c = V, F, cell
        self.g = collections.defaultdict(list)
        for k, f in enumerate(F):
            a, b, c = V[f[0]], V[f[1]], V[f[2]]
            lo = [int(math.floor(min(a[j], b[j], c[j]) / cell)) for j in range(3)]
            hi = [int(math.floor(max(a[j], b[j], c[j]) / cell)) for j in range(3)]
            if (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > 4096: hi = [lo[j] + 15 for j in range(3)]
            for x in range(lo[0], hi[0] + 1):
                for y in range(lo[1], hi[1] + 1):
                    for z in range(lo[2], hi[2] + 1): self.g[(x, y, z)].append(k)

    def near(self, p, rmax):
        c = [int(math.floor(p[j] / self.c)) for j in range(3)]
        best = None; seen = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in self.g.get((c[0] + dx, c[1] + dy, c[2] + dz), ()):
                        if k in seen: continue
                        seen.add(k); f = self.F[k]
                        d = pt_tri(p, self.V[f[0]], self.V[f[1]], self.V[f[2]])
                        if best is None or d < best: best = d
        return best if best is not None and best <= rmax else None


def cover(Vm, V, F, sample=3000, shift=(0.0, 0.0, 0.0)):
    """share of map vertices (a sample) within 25 / 100 / 400 units of a collision face after `shift`"""
    G = Grid(V, F)
    step = max(1, len(Vm) // sample)
    c = collections.Counter(); n = 0
    for v in Vm[::step]:
        p = (v[0] + shift[0], v[1] + shift[1], v[2] + shift[2]); n += 1
        d = G.near(p, 400.0)
        if d is None: continue
        for lim in (25, 100, 400):
            if d <= lim: c[lim] += 1
    return {('<=%d' % k): round(100.0 * c[k] / max(1, n), 1) for k in (25, 100, 400)}, n


# ------------------------------------------------------------------------------------------------ modes
def cmd_frame(a):
    U, Mp = load(a[0]), load(a[1])
    V, F, rows = collision(U)
    mm = map_mesh(Mp)
    print('unit %s: %d collision meshes, %d vertices, %d faces' % (a[0], len(rows), len(V), len(F)))
    for r in rows:
        print('   mesh [%d]+0x%x pos %s nodes %d faces %d verts %d bad %d +0x3c %08x +0x4c %d +0x50 %d +0x54 %s' % (
            r['mesh'][0], r['mesh'][1], fmt(r['pos']), r['nodes'], r['faces'], r['verts'], r['bad_faces'], r['w3c'],
            r['w4c'], r['w50'], r['w54']))
    lo, hi = bbox(V)
    print('   collision bbox (world) %s .. %s size %s' % (fmt(lo), fmt(hi), fmt([hi[j] - lo[j] for j in range(3)])))
    if mm is None: print('map %s: no mesh' % a[1]); return 0
    k, m, Vm, Fm, Nm = mm
    d = Mp[k].data
    hdr = struct.unpack_from('<12f', d, m[0])
    mlo, mhi = bbox(Vm)
    print('map %s: section %d mesh +0x%x nodes %d faces %d verts %d header bbox %s .. %s pos %s' % (
        a[1], k, m[0], m[1], m[2], m[3], fmt(hdr[0:3]), fmt(hdr[4:7]), fmt(hdr[8:11])))
    print('   map vertex bbox %s .. %s size %s' % (fmt(mlo), fmt(mhi), fmt([mhi[j] - mlo[j] for j in range(3)])))
    pos = hdr[8:11]
    Vw = [(v[0] + pos[0], v[1] + pos[1], v[2] + pos[2]) for v in Vm]
    if not F: return 0
    cv, n = cover(Vw, V, F)
    print('   translation 0: map vertices near a collision face (sample %d): %s' % (n, cv))
    cen = [((mlo[j] + mhi[j]) - (lo[j] + hi[j])) / 2 for j in range(3)]
    cv2, n2 = cover(Vw, V, F, shift=tuple(-x for x in cen))
    print('   translation by the bbox centre difference %s: %s' % (fmt(cen), cv2))
    org = origin(U)
    for sg, nm in ((1, 'map = collision + Level+0x80'), (-1, 'map = collision - Level+0x80')):
        cv3, n3 = cover(Vw, V, F, shift=tuple(-sg * x for x in org))
        print('   %s %s: %s' % (nm, fmt(org), cv3))
    # face byte 0 against the face normal (map) and against the nearest collision face's flags (collision + origin)
    def nz(a, b, c):
        u = [b[j] - a[j] for j in range(3)]; w = [c[j] - a[j] for j in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(x * x for x in n)) or 1.0
        return n[2] / ln
    by_slope = collections.defaultdict(collections.Counter)
    for f in Fm:
        i0, i1, i2 = struct.unpack_from('<3I', f, 0)
        z = nz(Vw[i0], Vw[i1], Vw[i2])
        cls_ = 'up' if z > 0.7 else 'down' if z < -0.7 else 'wall' if abs(z) < 0.3 else 'slope'
        by_slope[cls_][f[12]] += 1
    for c_, h_ in sorted(by_slope.items()):
        print('   map byte 0 for %-5s faces: %s' % (c_, sorted(h_.items(), key=lambda q: -q[1])[:8]))
    Vc = [(v[0] + org[0], v[1] + org[1], v[2] + org[2]) for v in V]
    G = Grid(Vc, F); same = collections.Counter(); step = max(1, len(Fm) // 2000)
    for f in Fm[::step]:
        i0, i1, i2 = struct.unpack_from('<3I', f, 0)
        p = tuple((Vw[i0][j] + Vw[i1][j] + Vw[i2][j]) / 3 for j in range(3))
        best, bk = None, None
        cc = [int(math.floor(p[j] / G.c)) for j in range(3)]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in G.g.get((cc[0] + dx, cc[1] + dy, cc[2] + dz), ()):
                        q = F[k]; dd = pt_tri(p, Vc[q[0]], Vc[q[1]], Vc[q[2]])
                        if best is None or dd < best: best, bk = dd, k
        if best is None or best > 25: same['no collision face within 25'] += 1; continue
        same['byte0 == collision flags & 0xff' if f[12] == F[bk][3] & 0xff else 'differs'] += 1
    print('   map face byte 0 vs the nearest collision face (<= 25 units): %s' % dict(same))
    fb = collections.Counter(bytes(f[12:20]).hex() for f in Fm)
    print('   map face bytes +0xc..+0x13 (top 6 of %d kinds): %s' % (len(fb), fb.most_common(6)))
    cb = collections.Counter('%08x %02x' % (f[3], f[4]) for f in F)
    print('   collision face flags / +0x10 (top 6 of %d kinds): %s' % (len(cb), cb.most_common(6)))
    for line in edge_bits(Vw, Fm): print('   ' + line)
    return 0


def normal(a, b, c):
    u = [b[j] - a[j] for j in range(3)]; w = [c[j] - a[j] for j in range(3)]
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    ln = math.sqrt(sum(x * x for x in n))
    return tuple(x / ln for x in n) if ln else None


def edge_kinds(V, tris):
    """per face, per edge k (k = 0: v0-v1, 1: v1-v2, 2: v2-v0): 'border' (no neighbour), 'flat' (neighbour normal
    within 5 deg), 'crease' (> 5 deg) - neighbours by shared vertex index pairs (and by position, rounded)"""
    key = lambda i: tuple(round(x, 1) for x in V[i])
    owners = collections.defaultdict(list)
    N = [normal(V[t[0]], V[t[1]], V[t[2]]) for t in tris]
    for fi, t in enumerate(tris):
        for k in range(3):
            a, b = key(t[k]), key(t[(k + 1) % 3])
            owners[frozenset((a, b))].append(fi)
    out = []
    for fi, t in enumerate(tris):
        row = []
        for k in range(3):
            e = frozenset((key(t[k]), key(t[(k + 1) % 3])))
            nb = [g for g in owners[e] if g != fi]
            if not nb: row.append('border'); continue
            n0 = N[fi]; ang = 0.0
            for g in nb:
                if n0 is None or N[g] is None: continue
                c = max(-1.0, min(1.0, sum(n0[j] * N[g][j] for j in range(3))))
                ang = max(ang, math.degrees(math.acos(c)))
            row.append(ang)
        out.append(row)
    return out


BINS = ((0.0, 0.01), (0.01, 1), (1, 5), (5, 10), (10, 20), (20, 30), (30, 45), (45, 181))
EDGE_DEG = 0.01         # an inner edge is a "feature" edge when its faces differ by more than this (real maps: 0 % at
                        # < 0.01 deg, 83-86 % at 0.01-1 deg, 100 % from 1 deg; borders 100 %)
STRAIGHT_DEG = 170.0    # two feature edges meeting at this angle or flatter continue a line (no corner)


def face_flags(V, tris):
    """face byte 0 from the geometry: bit 3 + k = edge k (v_k -> v_k+1) is a feature edge (border, or the neighbour
    face differs by > EDGE_DEG); bit k = vertex k is a corner: an end of a feature line (1 feature edge), a bend
    (2 feature edges meeting at < STRAIGHT_DEG) or a junction (3+) - by position, over the whole mesh"""
    kinds = edge_kinds(V, tris)
    key = lambda i: tuple(round(x, 1) for x in V[i])
    feat = collections.defaultdict(set)
    for t, row in zip(tris, kinds):
        for k in range(3):
            if row[k] == 'border' or row[k] > EDGE_DEG:
                a, b = key(t[k]), key(t[(k + 1) % 3])
                if a != b: feat[a].add(b); feat[b].add(a)
    corner = set()
    for p, nb in feat.items():
        if len(nb) != 2: corner.add(p); continue
        q, r = list(nb)
        u = [q[j] - p[j] for j in range(3)]; w = [r[j] - p[j] for j in range(3)]
        lu, lw = math.sqrt(sum(x * x for x in u)), math.sqrt(sum(x * x for x in w))
        if not lu or not lw: corner.add(p); continue
        c = max(-1.0, min(1.0, sum(u[j] * w[j] for j in range(3)) / (lu * lw)))
        if math.degrees(math.acos(c)) < STRAIGHT_DEG: corner.add(p)
    out = []
    for t, row in zip(tris, kinds):
        b = 0
        for k in range(3):
            if row[k] == 'border' or row[k] > EDGE_DEG: b |= 1 << (3 + k)
            if key(t[k]) in corner: b |= 1 << k
        out.append(b)
    return out


def cmd_bits(a):
    """face byte 0 rebuilt from the geometry (face_flags) against real maps: agreement per bit group"""
    for p in a:
        S = load(p); mm = map_mesh(S)
        if mm is None: print('%s: no mesh' % p); continue
        k, m, Vm, Fm, Nm = mm
        tris = [struct.unpack_from('<3I', f, 0) for f in Fm]
        pred = face_flags(Vm, tris)
        c = collections.Counter()
        for f, b in zip(Fm, pred):
            act = f[12]
            c['edge bits equal'] += (act >> 3) == (b >> 3); c['vertex bits equal'] += (act & 7) == (b & 7)
            c['byte equal'] += act == b
            for bit in range(6):
                c['bit%d %s' % (bit, 'tp' if (act >> bit) & 1 and (b >> bit) & 1 else 'fp' if (b >> bit) & 1 else
                                 'fn' if (act >> bit) & 1 else 'tn')] += 1
        # per vertex: actual flag (set in any face) against the incident feature edges by angle
        kinds = edge_kinds(Vm, tris)
        key = lambda i: tuple(round(x, 1) for x in Vm[i])
        inc = collections.defaultdict(dict); act_v = collections.Counter()
        for t, row, f in zip(tris, kinds, Fm):
            for k2 in range(3):
                a_, b_ = key(t[k2]), key(t[(k2 + 1) % 3]); x = 999.0 if row[k2] == 'border' else row[k2]
                for p_, q_ in ((a_, b_), (b_, a_)): inc[p_][q_] = max(inc[p_].get(q_, 0.0), x)
                if (f[12] >> k2) & 1: act_v[key(t[k2])] += 1
        for T in (0.01, 10, 30, 60):
            tab = collections.defaultdict(collections.Counter)
            for p_, nb in inc.items():
                n = sum(1 for x in nb.values() if x > T)
                tab[min(n, 5)][act_v[p_] > 0] += 1
            print('   vertex flag rate by incident edges > %g deg: %s' % (T, ', '.join('%d: %d%% of %d' % (
                n, round(100 * c[True] / max(1, c[True] + c[False])), c[True] + c[False]) for n, c in sorted(tab.items()))))
        # candidates for the header words +0x4c / +0x50
        d_ = S[k].data; h_ = m[0]
        w4c, w50 = struct.unpack_from('<2I', d_, h_ + 0x4c)
        area0 = sum(1 for t in tris if normal(Vm[t[0]], Vm[t[1]], Vm[t[2]]) is None)
        used = set(i for t in tris for i in t)
        dup = len(tris) - len(set(frozenset(t) for t in tris))
        leafs = [node(n)[4] for n in Nm if node(n)[4]]
        cand = {'zero-area faces': area0, 'unused vertices': len(Vm) - len(used), 'duplicate faces': dup,
                'byte0 == 0': sum(1 for f in Fm if f[12] == 0), 'leaves >= 4': sum(1 for x in leafs if x >= 4),
                'leaves >= 3': sum(1 for x in leafs if x >= 3), 'leaves': len(leafs),
                'max leaf': max(leafs), 'border edges': sum(1 for row in kinds for x in row if x == 'border')}
        print('   header +0x4c %d +0x50 %d; candidates %s' % (w4c, w50, cand))
        other = collections.Counter(bytes(f[13:20]).hex() for f in Fm)
        print('%s: faces %d, %s; bytes +0xd..+0x13: %s' % (p, len(Fm), {x: (round(100.0 * v / len(Fm), 1) if 'equal' in x else v)
                                                                       for x, v in sorted(c.items())}, other.most_common(3)))
    return 0


def edge_bits(Vw, Fm):
    """which bit of face byte 0 goes with which edge kind (tests the 'edge flags' reading of the 6 bits)"""
    tris = [struct.unpack_from('<3I', f, 0) for f in Fm]
    kinds = edge_kinds(Vw, tris)
    kd_of = lambda x: 'border' if x == 'border' else next('%g-%g' % b for b in BINS if b[0] <= x < b[1])
    # edge bits 3 + k against the dihedral angle of edge k
    st = collections.defaultdict(collections.Counter)
    for f, row in zip(Fm, kinds):
        for k, x in enumerate(row): st[kd_of(x)][(f[12] >> (3 + k)) & 1] += 1
    lines = ['edge bit (3 + k) set by edge kind: ' + ', '.join('%s %d%% of %d' % (kd, round(100 * st[kd][1] / max(1, st[kd][0] + st[kd][1])),
             st[kd][0] + st[kd][1]) for kd in ['border'] + ['%g-%g' % b for b in BINS])]
    # vertex bits k (vertex k = edges k and k-1) against: one of its two face edges is a border
    feat = lambda x: x == 'border'
    vt = collections.Counter()
    for f, row in zip(Fm, kinds):
        for k in range(3):
            want = feat(row[k]) or feat(row[(k + 2) % 3])
            vt[(want, (f[12] >> k) & 1)] += 1
    lines.append('vertex bit k vs "edge k or k-1 of this face is a border": %s' % dict(vt))
    # vertex bits against: the vertex lies on a border edge anywhere in the mesh (by position)
    key = lambda i: tuple(round(x, 1) for x in Vw[i])
    onb = set()
    for t, row in zip(tris, kinds):
        for k in range(3):
            if row[k] == 'border': onb.add(key(t[k])); onb.add(key(t[(k + 1) % 3]))
    vt2 = collections.Counter()
    for t, f in zip(tris, Fm):
        for k in range(3): vt2[(key(t[k]) in onb, (f[12] >> k) & 1)] += 1
    lines.append('vertex bit k vs "vertex on a border edge anywhere": %s' % dict(vt2))
    for thr in (0.5, 5, 20, 45):
        sharp = set()
        for t, row in zip(tris, kinds):
            for k in range(3):
                if row[k] == 'border' or row[k] > thr: sharp.add(key(t[k])); sharp.add(key(t[(k + 1) % 3]))
        vt3 = collections.Counter()
        for t, f in zip(tris, Fm):
            for k in range(3): vt3[(key(t[k]) in sharp, (f[12] >> k) & 1)] += 1
        lines.append('vertex bit k vs "vertex on an edge > %g deg anywhere": %s' % (thr, dict(vt3)))
    # vertex bit vs the largest angle among the vertex's edges in THIS face (k and k-1)
    vt4 = collections.defaultdict(collections.Counter)
    for f, row in zip(Fm, kinds):
        for k in range(3):
            x = [row[k], row[(k + 2) % 3]]
            m = 'border' if 'border' in x else kd_of(max(x))
            vt4[m][(f[12] >> k) & 1] += 1
    own = collections.Counter(); deg = collections.Counter()
    for t, f in zip(tris, Fm):
        for k in range(3):
            deg[t[k]] += 1
            if (f[12] >> k) & 1: own[t[k]] += 1
    hist = collections.Counter(own.get(i, 0) for i in deg)
    lines.append('faces per vertex index with the vertex bit set: %s (vertices %d)' % (sorted(hist.items()), len(deg)))
    eown = collections.Counter()
    for t, f in zip(tris, Fm):
        for k in range(3):
            if (f[12] >> (3 + k)) & 1: eown[frozenset((t[k], t[(k + 1) % 3]))] += 1
    lines.append('faces per flagged edge (index pair) with the edge bit: %s' % sorted(collections.Counter(eown.values()).items()))
    lines.append('vertex bit k by the larger angle of its two face edges: ' + ', '.join(
        '%s %d%% of %d' % (kd, round(100 * c[1] / max(1, c[0] + c[1])), c[0] + c[1]) for kd, c in sorted(vt4.items())))
    return lines


def node(n):
    a, b, idx = struct.unpack_from('<2fI', n, 0)
    return a, b, idx, n[12], n[13], n[14:16]


def face_ext(Vm, Fm, axis):
    out = []
    for f in Fm:
        i0, i1, i2 = struct.unpack_from('<3I', f, 0)
        vals = [Vm[i][axis] for i in (i0, i1, i2)]
        out.append((min(vals), max(vals)))
    return out


def subtree(N, k):
    """faces (first, count) of all leaves under node k"""
    st, out = [k], []
    while st:
        j = st.pop()
        a, b, idx, ax, cnt, pad = node(N[j])
        if cnt: out.append((idx, cnt))
        else: st += [j + 1, j + idx]
    return out


def cmd_bih(a):
    rc = 0
    for p in a:
        S = load(p); mm = map_mesh(S)
        if mm is None: print('%s: no mesh' % p); continue
        k, m, Vm, Fm, Nm = mm
        d = S[k].data; h = m[0]
        w = struct.unpack_from('<I', d, h + 0x3c)[0], struct.unpack_from('<I', d, h + 0x4c)[0], \
            struct.unpack_from('<I', d, h + 0x50)[0], struct.unpack_from('<2H', d, h + 0x54)
        ext = {ax: face_ext(Vm, Fm, ax) for ax in range(3)}
        rel = collections.Counter(); leafs = collections.Counter(); axes = collections.Counter(); pads = collections.Counter()
        depth = {0: 0}; maxd = 0; leaf_fl = collections.Counter()
        for j, n in enumerate(Nm):
            fa, fb, idx, ax, cnt, pad = node(n)
            pads[pad.hex()] += 1
            if cnt: leafs[cnt] += 1; leaf_fl['a=%g b=%g axis=%d' % (fa, fb, ax) if fa == 0 and fb == 0 else 'floats set'] += 1; continue
            axes[ax] += 1
            for c in (j + 1, j + idx): depth[c] = depth.get(j, 0) + 1; maxd = max(maxd, depth[c])
            if ax > 2: rel['axis > 2'] += 1; continue
            E = ext[ax]
            L = [E[i] for f0, c in subtree(Nm, j + 1) for i in range(f0, f0 + c)]
            Rr = [E[i] for f0, c in subtree(Nm, j + idx) for i in range(f0, f0 + c)]
            Lmax, Lmin = max(x[1] for x in L), min(x[0] for x in L)
            Rmax, Rmin = max(x[1] for x in Rr), min(x[0] for x in Rr)
            eps = 1e-3 * max(1.0, abs(fa), abs(fb))
            rel['a >= max(first child)'] += fa >= Lmax - eps
            rel['b <= min(second child)'] += fb <= Rmin + eps
            rel['a == max(first child)'] += abs(fa - Lmax) <= eps
            rel['b == min(second child)'] += abs(fb - Rmin) <= eps
            rel['a <= min(second child)'] += fa <= Rmin + eps
            rel['b >= max(first child)'] += fb >= Lmax - eps
            rel['first child below (Lmin <= Rmin)'] += Lmin <= Rmin
            rel['inner'] += 1
        print('%s: nodes %d faces %d verts %d, header +0x3c %08x +0x4c %d +0x50 %d +0x54 %s, max depth %d' % (
            p, len(Nm), len(Fm), len(Vm), w[0], w[1], w[2], w[3], maxd))
        print('   inner: %s' % dict(rel))
        print('   axes %s; leaf sizes %s; node bytes +0xe..+0xf %s; leaf floats %s' % (
            dict(axes), sorted(leafs.items())[:12], dict(pads), dict(leaf_fl)))
        print('   layout: header +0x%x, vertices +0x%x, faces +0x%x, nodes +0x%x, section %d B, header w %s, +0x58 %s' % (
            h, m[6][0], m[6][1], m[6][2], len(d), [struct.unpack_from('<f', d, h + o)[0] for o in (0xc, 0x1c, 0x2c)],
            d[h + 0x58:h + 0x60].hex()))
        cover_ = collections.Counter()
        for f0, c in subtree(Nm, 0):
            for i in range(f0, f0 + c): cover_[i] += 1
        print('   faces reached from the root: %d of %d, more than once %d' % (len(cover_), len(Fm), sum(1 for v in cover_.values() if v > 1)))
    return rc


# ------------------------------------------------------------------------------------------------ build
def build_tree(V, F):
    """KD nodes (BIH, the rule `bih` proved on the real maps: inner node {a = max extent of the first child (k + 1)
    along axis, b = min extent of the second child (k + index)}, leaf {0, 0, first face, 0, count}) and the face order"""
    ext = [[(min(V[i][ax] for i in f[:3]), max(V[i][ax] for i in f[:3])) for f in F] for ax in range(3)]
    cen = [[(e[0] + e[1]) / 2 for e in ext[ax]] for ax in range(3)]
    nodes, order = [], []
    depth = [0]

    def rec(ids, dep):
        depth[0] = max(depth[0], dep)
        k = len(nodes); nodes.append(None)
        lo = [min(ext[ax][i][0] for i in ids) for ax in range(3)]
        hi = [max(ext[ax][i][1] for i in ids) for ax in range(3)]
        ax = max(range(3), key=lambda q: hi[q] - lo[q])
        s = sorted(ids, key=lambda i: cen[ax][i])
        half = len(s) // 2
        if len(ids) <= LEAF_MAX or (cen[ax][s[0]] == cen[ax][s[-1]] and len(ids) <= 255):
            nodes[k] = ('leaf', len(order), len(ids)); order.extend(ids); return k
        A, B = s[:half], s[half:]
        a = max(ext[ax][i][1] for i in A); b = min(ext[ax][i][0] for i in B)
        rec(A, dep + 1); second = rec(B, dep + 1)
        nodes[k] = ('inner', a, b, second - k, ax); return k
    sys.setrecursionlimit(20000)
    rec(list(range(len(F))), 0)
    return nodes, order, depth[0]


def build(unit_src, map_in, out):
    """placeholder map + unit collision -> new map (rules proved by `frame` / `bih` / `bits` on real maps):
    vertices = collision (local + TerrainGroup position) + Level+0x80; mesh section layout as the real maps
    (vertices +0, faces, KD nodes, header 0x58 B at the end); map header section byte-identical except its pointer
    +0 to the mesh header (external relocation, moved to the new header offset)"""
    U = load(unit_src); Mp = DW.read(open(map_in, 'rb').read(), 'le')
    V0, F0, rows = collision(U)
    if not F0: raise SystemExit('%s: no collision faces' % unit_src)
    org = origin(U)
    # world + origin, rounded to the float32 the file holds (the zero-area test must see the written values)
    V = [struct.unpack('<3f', struct.pack('<3f', v[0] + org[0], v[1] + org[1], v[2] + org[2])) for v in V0]
    F = [f for f in F0 if normal(V[f[0]], V[f[1]], V[f[2]]) is not None]      # zero-area faces dropped
    used = sorted(set(i for f in F for i in f[:3]))
    remap = {i: j for j, i in enumerate(used)}
    V = [V[i] for i in used]; F = [(remap[f[0]], remap[f[1]], remap[f[2]]) for f in F]
    if len(V) > VERT_MAX: raise SystemExit('%s: %d vertices > %d (u16 reveal count)' % (unit_src, len(V), VERT_MAX))
    S = [Sec(s.type, s.id, s.data, s.reloc) for s in Mp.sections]
    mm = map_mesh(S)
    if mm is None: raise SystemExit('%s: no mesh section' % map_in)
    k, m, Vm0, Fm0, Nm0 = mm
    old = Mp.sections[k].data; h0 = m[0]
    r0 = R.parse(Mp.sections[0].reloc, 'le')
    if len(Mp.sections) != 2 or k != 1 or h0 + 0x58 != len(old) or [(si, so, do) for si, so, do in r0.external] != [(1, 0, h0)]:
        raise SystemExit('%s: not the real-map layout (2 sections, header at the end, section 0 +0 -> header)' % map_in)
    nodes, order, maxd = build_tree(V, F)
    flags = face_flags(V, F)
    lo, hi = bbox(V)
    vo = 0; fo = 16 * len(V); no = fo + 20 * len(F); h = no + 16 * len(nodes)
    d = bytearray(h + 0x58)
    for j, v in enumerate(V): struct.pack_into('<4f', d, vo + 16 * j, v[0], v[1], v[2], 0.0)
    for j, i in enumerate(order):
        f = F[i]; struct.pack_into('<3I2B6x', d, fo + 20 * j, f[0], f[1], f[2], flags[i], 0xff)
    for j, n in enumerate(nodes):
        if n[0] == 'leaf': struct.pack_into('<2fI4B', d, no + 16 * j, 0.0, 0.0, n[1], 0, n[2], 0, 0)
        else: struct.pack_into('<2fI4B', d, no + 16 * j, n[1], n[2], n[3], n[4], 0, 0, 0)
    # header: bbox min / max (w as the placeholder), +0x20 position and +0x3c as the placeholder, pointers, counts,
    # +0x4c zero-area faces (0: dropped; caverns 4 = its 4 zero-area faces), +0x50 as the placeholder (0; meaning open),
    # +0x54 {vertexType 1, height = tree depth + 1} (4 real maps)
    struct.pack_into('<4f', d, h + 0x00, lo[0], lo[1], lo[2], struct.unpack_from('<f', old, h0 + 0x0c)[0])
    struct.pack_into('<4f', d, h + 0x10, hi[0], hi[1], hi[2], struct.unpack_from('<f', old, h0 + 0x1c)[0])
    d[h + 0x20:h + 0x30] = old[h0 + 0x20:h0 + 0x30]
    struct.pack_into('<3I', d, h + 0x30, PH, PH, PH)
    d[h + 0x3c:h + 0x40] = old[h0 + 0x3c:h0 + 0x40]
    struct.pack_into('<4I', d, h + 0x40, len(nodes), len(F), len(V), 0)
    d[h + 0x50:h + 0x54] = old[h0 + 0x50:h0 + 0x54]
    struct.pack_into('<2H', d, h + 0x54, 1, maxd + 1)
    r = R.Reloc(internal=[(h + 0x30, vo), (h + 0x34, fo), (h + 0x38, no)])
    Mp.sections[k].data = bytes(d); Mp.sections[k].reloc = R.write(r, 'le')
    r0.external = [(1, 0, h)]
    Mp.sections[0].reloc = R.write(r0, 'le')
    raw = Mp.write('le')
    blob = DW.cdrm_encode(raw, 'le') if open(map_in, 'rb').read(4) == b'CDRM' else raw
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(blob)
    return dict(unit=unit_src, map_in=map_in, out=out, meshes=len(rows), verts=len(V), faces=len(F), nodes=len(nodes),
                height=maxd + 1, dropped_zero_area=len(F0) - len(F), origin=list(org), bbox=[lo, hi],
                md5=hashlib.md5(blob).hexdigest(), placeholder=dict(verts=len(Vm0), faces=len(Fm0)),
                mesh_rows=[dict(pos=r_['pos'], faces=r_['faces'], verts=r_['verts']) for r_ in rows])


PH = 0xBEEBBEEB


def check(path, ref_in=None):
    S = load(path); probs = []
    mm = map_mesh(S)
    if mm is None: return ['no mesh'], {}
    k, m, V, F, N = mm
    h, nn, nf, nv, vt, fs, (vo, fo, no) = m
    if nv > VERT_MAX: probs.append('vertices %d > %d' % (nv, VERT_MAX))
    if vt != 1 or fs != 20: probs.append('vertexType %d / face stride %d' % (vt, fs))
    for j, f in enumerate(F):
        if max(struct.unpack_from('<3I', f, 0)) >= nv: probs.append('face %d index out of range' % j); break
    seen = collections.Counter(); bad = 0
    for j, n in enumerate(N):
        a, b, idx, ax, cnt, pad = node(n)
        if cnt:
            if idx + cnt > nf: bad += 1
            for i in range(idx, idx + cnt): seen[i] += 1
        elif idx == 0 or j + idx >= nn or j + 1 >= nn or ax > 2: bad += 1
    if bad: probs.append('%d bad KD nodes' % bad)
    if len(seen) != nf or any(v != 1 for v in seen.values()): probs.append('faces in leaves: %d of %d, repeated %d' % (
        len(seen), nf, sum(1 for v in seen.values() if v > 1)))
    # reachability + float rule (a >= max of the first child, b <= min of the second, along axis)
    ext = {ax: face_ext(V, F, ax) for ax in range(3)}
    reach = collections.Counter(); rule_bad = 0; maxd = 0
    st = [(0, 0)]
    while st:
        j, dep = st.pop(); a, b, idx, ax, cnt, pad = node(N[j]); maxd = max(maxd, dep)
        if cnt:
            for i in range(idx, idx + cnt): reach[i] += 1
            continue
        for c in (j + 1, j + idx): st.append((c, dep + 1))
        L = [ext[ax][i] for f0, c in subtree(N, j + 1) for i in range(f0, f0 + c)]
        Rr = [ext[ax][i] for f0, c in subtree(N, j + idx) for i in range(f0, f0 + c)]
        if a < max(x[1] for x in L) - 1e-3 or b > min(x[0] for x in Rr) + 1e-3: rule_bad += 1
    if len(reach) != nf: probs.append('faces reachable from the root %d of %d' % (len(reach), nf))
    if rule_bad: probs.append('%d inner nodes whose floats do not bound their children' % rule_bad)
    lo, hi = bbox(V); hb = struct.unpack_from('<8f', S[k].data, h)
    if any(abs(hb[j] - lo[j]) > 1e-2 or abs(hb[4 + j] - hi[j]) > 1e-2 for j in range(3)): probs.append('header bbox != vertices')
    vt_, height = struct.unpack_from('<2H', S[k].data, h + 0x54)
    if height != maxd + 1: probs.append('header height %d, tree depth + 1 = %d' % (height, maxd + 1))
    zero = sum(1 for f in F if normal(*[V[i] for i in struct.unpack_from('<3I', f, 0)]) is None)
    if struct.unpack_from('<I', S[k].data, h + 0x4c)[0] != zero: probs.append('header +0x4c != %d zero-area faces' % zero)
    r0 = R.parse(S[0].reloc, 'le')
    if k != 1 or [x for x in r0.external] != [(1, 0, h)]: probs.append('section 0 +0 does not point at the mesh header')
    if ref_in is not None:
        Ri = load(ref_in); ri = R.parse(Ri[0].reloc, 'le')
        if Ri[0].data != S[0].data or ri.internal != r0.internal or [x[:2] for x in ri.external] != [x[:2] for x in r0.external]:
            probs.append('map header section differs from the input (beyond the mesh pointer)')
        if len(Ri) != len(S) or (Ri[0].type, Ri[0].id, Ri[1].type, Ri[1].id) != (S[0].type, S[0].id, S[1].type, S[1].id):
            probs.append('sections differ from the input')
    return probs, dict(nodes=nn, faces=nf, verts=nv, height=height)


def main(a):
    if not a: sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'frame' and len(a) == 3: return cmd_frame(a[1:])
    if cmd == 'bih' and len(a) >= 2: return cmd_bih(a[1:])
    if cmd == 'bits' and len(a) >= 2: return cmd_bits(a[1:])
    if cmd == 'big' and len(a) >= 2:
        # the largest collision faces of a unit (world + origin): area, normal z, height, mesh group, flags
        U = load(a[1]); V0, F0, rows = collision(U); org = origin(U)
        V = [(v[0] + org[0], v[1] + org[1], v[2] + org[2]) for v in V0]
        bounds = []; acc = 0
        for r_ in rows: bounds.append((acc, acc + r_['verts'], r_)); acc += r_['verts']
        out = []
        for f in F0:
            P = [V[i] for i in f[:3]]
            u = [P[1][j] - P[0][j] for j in range(3)]; w = [P[2][j] - P[0][j] for j in range(3)]
            c = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            ar = math.sqrt(sum(x * x for x in c)) / 2
            mi = next(j for j, (s0, s1, r_) in enumerate(bounds) if s0 <= f[0] < s1)
            out.append((ar, c[2] / (2 * ar) if ar else 0, sum(p[2] for p in P) / 3, mi, f[3], f[4]))
        out.sort(reverse=True)
        lo, hi = bbox(V)
        print('%s: %d faces, z %.0f .. %.0f; largest:' % (a[1], len(F0), lo[2], hi[2]))
        for ar, nz_, z, mi, fl, b10 in out[:int(a[2]) if len(a) > 2 else 12]:
            print('   area %.3g m2-ish (%.0f units2) nz %+.2f z %.0f mesh %d (faces %d) flags %08x +0x10 %02x' % (
                ar / 290.0 ** 2, ar, nz_, z, mi, bounds[mi][2]['faces'], fl, b10))
        return 0
    if cmd == 'pic' and len(a) >= 3:
        # top view (x right, y up) of a map mesh as PNG: grey = up-facing, blue = walls, dark = down-facing, z-buffer
        # from above; read-only for the map, writes only OUT.png
        import zlib
        S = load(a[1]); mm = map_mesh(S); size = int(a[3]) if len(a) > 3 else 600
        k, m, Vm, Fm, Nm = mm
        lo, hi = bbox(Vm); span = max(hi[0] - lo[0], hi[1] - lo[1]) or 1.0
        sc = (size - 1) / span
        img = bytearray(b'\x10\x10\x18' * size * size); zb = [-1e30] * (size * size)
        for f in Fm:
            t = struct.unpack_from('<3I', f, 0); P = [Vm[i] for i in t]
            n = normal(*P)
            if n is None: continue
            col = (200, 200, 200) if n[2] > 0.5 else (60, 70, 90) if n[2] < -0.5 else (70, 140, 230)
            xs = [(p[0] - lo[0]) * sc for p in P]; ys = [(hi[1] - p[1]) * sc for p in P]; zs = [p[2] for p in P]
            x0, x1 = max(0, int(min(xs))), min(size - 1, int(max(xs)) + 1)
            y0, y1 = max(0, int(min(ys))), min(size - 1, int(max(ys)) + 1)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    if not den:
                        if (px, py) != (int(xs[0]), int(ys[0])): continue
                        l0, l1, l2 = 1.0, 0.0, 0.0
                    else:
                        l0 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / den
                        l1 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / den
                        l2 = 1 - l0 - l1
                        if min(l0, l1, l2) < -0.02: continue
                    z = l0 * zs[0] + l1 * zs[1] + l2 * zs[2]
                    q = py * size + px
                    if z > zb[q]: zb[q] = z; img[3 * q:3 * q + 3] = bytes(col)
        raw = b''.join(b'\0' + bytes(img[3 * size * r:3 * size * (r + 1)]) for r in range(size))
        chunk = lambda t, d_: struct.pack('>I', len(d_)) + t + d_ + struct.pack('>I', zlib.crc32(t + d_) & 0xffffffff)
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)) + \
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
        open(a[2], 'wb').write(png)
        print('%s -> %s (%d x %d, %d faces, extent %s .. %s)' % (a[1], a[2], size, size, len(Fm), fmt(lo), fmt(hi)))
        return 0
    if cmd == 'portals' and len(a) >= 2:
        # map header section: +8 portal count, +0xc -> entries of 32 B {-> target name, id, id, 0, vec4 point}:
        # each portal point against the map's own mesh (distance to the nearest face) - the frame check per unit
        for p in a[1:]:
            S = load(p); mm = map_mesh(S)
            d0 = S[0].data; it0 = dict(R.parse(S[0].reloc, 'le').internal)
            n = struct.unpack_from('<I', d0, 8)[0]; t = it0.get(0xc)
            if mm is None or t is None: print('%s: no mesh / no portal list' % p); continue
            k, m, Vm, Fm, Nm = mm
            tris = [struct.unpack_from('<3I', f, 0) for f in Fm]
            G = Grid(Vm, tris, cell=1000.0)
            parts = []
            for j in range(n):
                e = t + 32 * j; nm_at = it0.get(e)
                nm = d0[nm_at:d0.index(b'\0', nm_at)].decode('latin1') if nm_at is not None else '?'
                pt = struct.unpack_from('<3f', d0, e + 0x10)
                dist = G.near(pt, 3000.0)
                parts.append('%s %s: %s' % (nm, fmt(pt), 'no face within 3000' if dist is None else '%.0f units' % dist))
            print('%s: %d portals; %s' % (os.path.basename(p), n, '; '.join(parts)))
        return 0
    if cmd == 'hdr' and len(a) >= 2:
        for p in a[1:]:
            S = load(p)
            for k, s in enumerate(S):
                r = R.parse(s.reloc, 'le')
                print('%s [%d] type %d id %d size %d internal %s external %s id refs %s' % (
                    p, k, s.type, s.id, len(s.data or b''), r.internal[:6], r.external[:6], (r.idref + r.idref_a)[:6]))
                if k == 0:
                    d = s.data
                    for o in range(0, len(d) - 3, 4):
                        w = struct.unpack_from('<I', d, o)[0]; f = struct.unpack_from('<f', d, o)[0]
                        print('   +0x%02x %08x %12g %s' % (o, w, f, d[o:o + 4].decode('latin1').replace('\0', '.')))
        return 0
    if cmd == 'build' and len(a) == 4:
        info = build(a[1], a[2], a[3]); probs, c = check(a[3], a[2])
        print('%s: %s %s' % ('ok' if not probs else 'FAIL', info, probs))
        if probs: os.remove(a[3])
        return 1 if probs else 0
    if cmd == 'check' and len(a) >= 2:
        rc = 0
        for p in a[1:]:
            probs, c = check(p); print('%s %s %s %s' % ('ok  ' if not probs else 'FAIL', p, c, probs)); rc |= bool(probs)
        return rc
    if cmd == 'batch' and len(a) >= 5:
        rep = None
        if '--report' in a: k = a.index('--report'); rep = a[k + 1]; del a[k:k + 2]
        ud, md, od = a[1], a[2], a[3]; rows = []; rc = 0
        for nm in a[4:]:
            u, mi, mo = os.path.join(ud, nm + '.drm'), os.path.join(md, nm + '_map.drm'), os.path.join(od, nm + '_map.drm')
            try:
                info = build(u, mi, mo); probs, c = check(mo, mi)
            except SystemExit as e:
                info, probs = dict(unit=u), [str(e)]
            if probs and os.path.isfile(mo): os.remove(mo)
            rc |= bool(probs); rows.append(dict(name=nm, ok=not probs, problems=probs, **{k: v for k, v in info.items() if k != 'bbox'}))
            print('%s %s %s %s' % ('ok  ' if not probs else 'FAIL', nm, {k: v for k, v in info.items() if k in ('verts', 'faces', 'nodes', 'md5')}, probs))
        if rep: json.dump(dict(tool='tools/sonar_map_build.py batch', leaf_max=LEAF_MAX, edge_deg=EDGE_DEG,
                               straight_deg=STRAIGHT_DEG, rows=rows), open(rep, 'w'), indent=1)
        return rc
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
