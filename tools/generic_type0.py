"""General (type 0) sections: learned word classes (generic_learn) + unit-level global id spaces.

Unit DRMs carry ids of three GLOBAL numbering spaces that differ between Xbox and PC (tools/unit_ids.py):
  110 unit   (StreamUnitID = objlist.dat record index; name-based map incl. DLC units)
  111 portal (StreamUnitPortal ids)       112 tguid (TerrainGroup.uniqueID)
Two mechanisms:
  * exact structural fix-up of the known fields (unit_ids.unit_fields: Level+0x4c, Level+0x94 portal-id list,
    portal +0x80/+0x82/+0x84, TerrainGroup+0x28)        -> fix_unit_fields(xsecs, out_sections, ids)
  * learned classes id16a/id16b/id32 for the spaces + 'K:<pc word>' constants (build-tool garbage that PC
    has as one constant, e.g. 0x1dbbda98 -> 0x0686da98) at label keys, trained on type-0 pairs only
    (work/generic/type0_table.pkl); labels use root ('LVL',) for a unit's Level section so keys do not depend
    on the Level size (= portal count).
DlcIds maps 110/111/112 through work/generic/unit_idmaps.json (unknown portal/tguid values = DLC-new, kept:
DLC uses portal 162+ / tguid 566+, PC max 161 / 547 -> no collision).
Usage: tools/venv/bin/python -I tools/generic_type0.py [eval|save]
"""
import sys, os, struct, json, collections, pickle, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
import unit_ids as U
W = G.W
TABLE0 = os.path.join(W, 'type0_table.pkl')
UNIT, PORTAL, TGUID = 110, 111, 112
INTRO = 113
REC = 114
NODE = 115
SPACE = {'unit': UNIT, 'portal': PORTAL, 'tguid': TGUID, 'intro': INTRO, 'object': 11, 'rec': REC, 'node': NODE, 'intro_n': INTRO}

def space_maps():
    d = json.load(open(U.OUT))
    return {SPACE[k]: {int(a): b for a, b in m.items()} for k, m in d.items() if k != 'object'}

_INEW = {}
def intro_new(m, x):
    """Intro uniqueID not in the base map (DLC-new): kept unless it equals a PC intro id (DLC ids 6713..12240 partly
    reuse gaps of the Xbox base range; 1 collides) -> 20000 + x."""
    if x in _INEW: return _INEW[x]
    used = set(m.values())
    if x not in used: _INEW[x] = x; return x
    _INEW[x] = 20000 + x          # deterministic, above every Xbox/PC/DLC intro id seen (max 12240)
    return _INEW[x]

_SK = {}
def interp(t, m, x):
    """unmapped id inside the base range of a block-numbered space (intro 113): if both mapped neighbours have the same
    PC-Xbox offset, use it (the spaces are renumbered in contiguous level blocks); else None."""
    import bisect
    ks = _SK.get(t)
    if ks is None: ks = _SK[t] = sorted(m)
    k = bisect.bisect_left(ks, x)
    if 0 < k < len(ks):
        a, b = ks[k - 1], ks[k]
        if m[a] - a == m[b] - b: return x + m[a] - a
    return None

def level_roots(secs, e='be'):
    return {0: ('LVL',)} if U.level_info(secs, e) else None

def labels(secs, e='be', types=None):
    G.ROOT_EXACT_DTP = True
    try:
        return G.drm_labels(secs, e, types, roots=level_roots(secs, e))
    finally:
        G.ROOT_EXACT_DTP = False

# ------------------------------------------------------------------------------- classes
def word_classes0(xw, pw, idm):
    cs = G.word_classes(xw, pw, idm)
    if cs is None: return None
    v, = struct.unpack('>I', xw); pv, = struct.unpack('<I', pw)
    for t in (UNIT, TGUID, INTRO, REC, NODE, PORTAL):
        m = idm.get(t)
        if m and v in m and m[v] == pv and m[v] != v: cs.append('id32:%d' % t)
    a, b = struct.unpack('>HH', xw); pa, pb = struct.unpack('<HH', pw)
    for t in (UNIT, PORTAL, REC, 11):
        m = idm.get(t)
        if not m: continue
        ma = a in m and m[a] == pa and m[a] != a
        mb = b in m and m[b] == pb and m[b] != b
        if t != 11:
            if ma and b == pb: cs.append('id16a:%d' % t)
            if mb and a == pa: cs.append('id16b:%d' % t)
            if ma and mb: cs.append('id16ab:%d' % t)
        if mb and xw[0:2] == pw[0:2]: cs.append('rid16b:%d' % t)      # 2 raw bytes + mapped u16
        if ma and xw[2:4] == pw[2:4]: cs.append('id16ar:%d' % t)      # mapped u16 + 2 raw bytes
    if not cs: cs.append('K:%08x' % pv)
    return cs

K_MIN = 20          # minimum votes for a learned constant ('K:') class

class Table0(G.Table):
    def best(self, key):
        c = self.v.get(key)
        if not c: return None
        tot = sum(c.values())
        items = [kv for kv in c.items() if kv[0] != '?' and not kv[0].startswith('K:')]
        k = [kv for kv in c.items() if kv[0].startswith('K:')]
        if k:
            kb = max(k, key=lambda kv: kv[1])
            if kb[1] >= K_MIN and kb[1] >= 0.9 * tot: return kb[0]
        if not items: return None
        return max(items, key=lambda kv: (kv[1], -G.PREF.get(kv[0], 9)))[0]

def apply_word(xw, c, ids):
    if c.startswith('K:'):
        return struct.pack('<I', int(c[2:], 16)) if xw not in (b'\0\0\0\0', b'\xff\xff\xff\xff') else xw
    if c.startswith('rid16b:'):
        b, = struct.unpack('>H', xw[2:4]); t = int(c[7:])
        return xw[0:2] + struct.pack('<H', ids(t, b) & 0xffff if b not in (0, 0xffff) else b)
    if c.startswith('id16ar:'):
        a, = struct.unpack('>H', xw[0:2]); t = int(c[7:])
        return struct.pack('<H', ids(t, a) & 0xffff if a not in (0, 0xffff) else a) + xw[2:4]
    return G.apply_word(xw, c, ids)

def shape(xw):
    """coarse value shape of an Xbox word (BE): lets one label key hold e.g. floats AND u16 pairs AND byte flags"""
    v = struct.unpack('>I', xw)[0]
    if v == 0 or v == 0xffffffff: return 'Z'
    if v & 0x00ffffff == 0: return 'B0'
    if v & 0xff00ffff == 0: return 'B1'
    if v & 0xffff00ff == 0: return 'B2'
    if v & 0xffffff00 == 0: return 'B3'
    e = (v >> 23) & 0xff
    if 100 <= e <= 150: return 'F'
    a, b = v >> 16, v & 0xffff
    if a and b and a < 0x4000 and b < 0x4000: return 'HH'
    if a == 0: return 'H0'
    if b == 0: return '0H'
    return 'O'

def lookup(T0, T, key, ck, xw=None):
    if xw is not None:
        c = T0.best(('S', key, shape(xw)))
        if c is not None: return c, 'shape'
        c = T0.best(('SC',) + ck + (shape(xw),))
        if c is not None: return c, 'shape-coarse'
    for k, src in ((key, 'label'), (G.mid(key), 'mid'), (('C',) + ck, 'coarse')):
        c = T0.best(k)
        if c is not None: return c, src
    if xw is not None:                       # unseen structure: global per-shape majority before the region majority
        c = T0.best(('SG', shape(xw)))
        if c in ('s32', 's16', 'b2s16', 's16b2'): return c, 'shape-global'
    c = T0.best(('R', key[0]))
    if c is not None: return c, 'region'
    if T is not None:
        return G.lookup(T, key, ck)
    return None, 'fallback'

# build-tool garbage words (heap-pointer-like) that PC always has as one constant; each Xbox value below occurs ONLY
# in such fields in all base pairs (1139/398/152/48/44/18 occurrences, 100% consistent)
VMAP = {0x00119c48: 0x0011ab28, 0x00118fd8: 0x0011ab28, 0x00116de4: 0x00117cc4, 0x00119b54: 0x0011aa34,
        0x1dbbda98: 0x0686da98, 0x0cf2da98: 0x0686da98, 0x0516da98: 0x0686da98}

def convert_section0(x, regions, rel, T0, ids, T=None, stats=None, pd=None):
    out = bytearray(x)
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    for w, key, ck in G.word_keys(len(x), regions):
        if w in skip: continue
        xw = x[w:w + 4]
        c, src = lookup(T0, T, key, ck, xw)
        if c is None:
            src = 'fallback'; c = 'raw' if G.is_text(xw) and xw != xw[::-1] else 's32'
        if stats is not None: stats[src] += 1
        v = VMAP.get(struct.unpack('>I', xw)[0])
        out[w:w + 4] = struct.pack('<I', v) if v is not None else apply_word(xw, c, ids)
        if pd is not None and stats is not None and out[w:w + 4] != pd[w:w + 4]:
            stats['bad_src', src, shape(xw), c] += 1
    for o in rel.pointer_offsets():
        out[o:o + 4] = x[o:o + 4][::-1]
    for o, t in rel.id_offsets().items():
        v, = struct.unpack_from('>I', x, o)
        struct.pack_into('<I', out, o, ids(t, v) if v not in (0, 0xffffffff) else v)
    return bytes(out)

def fix_unit_fields(xsecs, datas, ids):
    """datas: list of converted section data (bytes, PC layout = Xbox layout for type 0) -> patched list."""
    f = U.unit_fields(xsecs, 'be')
    if not f: return datas
    datas = list(datas)
    for si, o, w, sp in f:
        d = xsecs[si]['data']
        if d is None or o + (2 if w == 'u16' else 4) > len(d): continue
        v = U.read(d, o, w, 'be')
        nv = ids(SPACE[sp], v) if v not in (0, 0xffff, 0xffffffff) else v
        b = bytearray(datas[si])
        struct.pack_into('<H' if w == 'u16' else '<I', b, o, nv & (0xffff if w == 'u16' else 0xffffffff))
        datas[si] = bytes(b)
    return datas

def name_stream_patches(secs):
    """Portal/cell name stream (in the section at Level+0x90, block at its +0xc): u32 0, u32 LITTLE-endian offsets[n] (LE on
    BOTH platforms), then a byte pool 'unitname\\0' + records {char name[] NUL, u32 value (platform endian, unaligned), u8}
    at pool+offs[k].  Returns {sec: [(start, bytes)]} = the PC bytes of the whole block."""
    out = {}
    for s in secs:
        d = s['data']
        if s['type'] != 0 or d is None: continue
        q = d.find(b'unitname\x00')
        while q >= 8:
            t = q - 4; offs = []
            while t >= 4:
                v = struct.unpack_from('<I', d, t)[0]
                offs.insert(0, v)
                if v == 9: break
                t -= 4
            if offs and offs[0] == 9 and all(a < b for a, b in zip(offs, offs[1:])) and q + offs[-1] < len(d):
                b = bytearray(d[t:]); ok = True; end = 0
                for o in offs:
                    e = d.find(b'\x00', q + o)
                    if e < 0 or e + 5 > len(d): ok = False; break
                    v = d[e + 1:e + 5]; b[e + 1 - t:e + 5 - t] = v[::-1]; end = e + 6
                if ok: out.setdefault(s['i'], []).append((t, bytes(b[:end - t])))
            q = d.find(b'unitname\x00', q + 1)
    return out

def apply_overrides(xsecs, datas, ids):
    """structural overrides for converted type-0 data: collision mesh arrays + unit id fields + name streams."""
    datas = list(datas)
    for si, l in name_stream_patches(xsecs).items():
        b = bytearray(datas[si])
        for t, pb in l: b[t:t + len(pb)] = pb
        datas[si] = bytes(b)
    ov = mesh_overrides(xsecs, 'be')
    if ov:
        by = collections.defaultdict(list)
        for (si, o), c in ov.items(): by[si].append((o, c))
        for si, l in by.items():
            x = xsecs[si]['data']; b = bytearray(datas[si])
            rel = R.parse(xsecs[si]['reloc'], 'be'); skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            for o, c in l:
                if o not in skip and o + 4 <= len(x): b[o:o + 4] = apply_word(x[o:o + 4], c, ids)
            datas[si] = bytes(b)
    return fix_unit_fields(xsecs, datas, ids)

def _khash(k):
    import hashlib
    return int.from_bytes(hashlib.blake2b(repr(k).encode(), digest_size=8).digest(), 'little')

class SlimTable:
    """best-class lookup from a compact index (sorted uint64 key hashes + class codes), built by slim()"""
    def __init__(self, path):
        import numpy as np
        z = np.load(path, allow_pickle=False)
        self.h, self.c = z['h'], z['c']
        self.vocab = json.load(open(path[:-4] + '_vocab.json'))
        self._np = np
    def best(self, key):
        hv = self._np.uint64(_khash(key))
        i = int(self._np.searchsorted(self.h, hv))
        if i < len(self.h) and self.h[i] == hv:
            v = self.vocab[int(self.c[i])]
            return v if v != '' else None
        return None

def slim(pkl, out):
    """Table0 pickle -> npz (keys whose best() is None are dropped)"""
    import numpy as np
    T = Table0(); T.v.update(pickle.load(open(pkl, 'rb')))
    best = {}
    for k in list(T.v):
        b = T.best(k)
        if b is not None: best[k] = b
    vocab = sorted(set(best.values()))
    code = {v: i for i, v in enumerate(vocab)}
    h = np.fromiter((_khash(k) for k in best), dtype=np.uint64, count=len(best))
    c = np.fromiter((code[v] for v in best.values()), dtype=np.uint32, count=len(best))
    o = np.argsort(h)
    np.savez(out, h=h[o], c=c[o])
    json.dump(vocab, open(out[:-4] + '_vocab.json', 'w'))
    return len(best), int((h[o][1:] == h[o][:-1]).sum())

def _load(name):
    npz = os.path.join(W, name + '_slim.npz'); pkl = os.path.join(W, name + '.pkl')
    if os.path.exists(npz) and (not os.path.exists(pkl) or os.path.getmtime(npz) >= os.path.getmtime(pkl)):
        return SlimTable(npz)
    if os.path.exists(pkl):
        T = Table0(); T.v.update(pickle.load(open(pkl, 'rb'))); return T
    return None

_T7 = None
def table7():
    global _T7
    if _T7 is None: _T7 = _load('type7_table')
    return _T7

_T0 = None
def table0():
    global _T0
    if _T0 is None: _T0 = _load('type0_table')
    return _T0

# ------------------------------------------------------------------------------- train / evaluate
def train(P, names, idm, types=(0,)):
    from generic_ids import section_matches
    T = Table0()
    for nm in names:
        (xh, sx), (ph, sp) = P[nm]
        labs = None
        for i, j, stg in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            if a['type'] not in types or a['size'] != b['size'] or a['data'] is None or stg not in ('A', 'K'): continue
            if labs is None: labs = labels(sx, 'be', types)
            rel = R.parse(a['reloc'], 'be')
            skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            da, db = a['data'], b['data']
            for w, key, ck in G.word_keys(a['size'], labs[i]):
                if w in skip: continue
                cs = word_classes0(da[w:w + 4], db[w:w + 4], idm)
                if cs is None: continue
                sh = shape(da[w:w + 4])
                for k in (key, G.mid(key), ('R', key[0]), ('C',) + ck, ('S', key, sh), ('SC',) + ck + (sh,), ('SG', sh)): T.add(k, cs)
    return T

def evaluate(P, names, T0, ids, idm, T=None, types=(0,), detail=None, fix=True):
    from generic_ids import section_matches
    st = collections.Counter()
    for nm in names:
        (xh, sx), (ph, sp) = P[nm]
        labs = None
        conv = {}
        for i, j, stg in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            if a['type'] not in types or a['data'] is None or b['data'] is None: continue
            if a['size'] != b['size']: st['size_differs'] += 1; continue
            if labs is None: labs = labels(sx, 'be', types)
            conv[i] = (j, stg, convert_section0(a['data'], labs[i], R.parse(a['reloc'], 'be'), T0, ids, T, st, b['data']))
        if fix and conv:
            datas = [conv[i][2] if i in conv else (s['data'] or b'') for i, s in enumerate(sx)]
            datas = apply_overrides(sx, datas, ids)
            conv = {i: (j, stg, datas[i]) for i, (j, stg, _) in conv.items()}
        for i, (j, stg, d) in conv.items():
            b = sp[j]['data']
            k = 'A' if stg == 'A' else 'other'
            st[k, 'n'] += 1
            if d == b: st[k, 'exact'] += 1
            else:
                bw = sum(1 for q in range(0, len(d), 4) if d[q:q + 4] != b[q:q + 4])
                st[k, 'badw'] += bw; st[k, 'bytes'] += len(d)
                if detail is not None: detail.append((nm, i, j, stg, bw))
    return st

def report(st, title):
    for k in ('A', 'other'):
        n = st[k, 'n']
        if n: print('-- %s [%s-matched]: %d sections, exact %d = %.2f%%, wrong words %d' % (title, k, n, st[k, 'exact'], 100. * st[k, 'exact'] / n, st[k, 'badw']))

def idmaps():
    from convert_generic import IdMapper
    idm = IdMapper().m
    idm.update(space_maps())
    return idm

# ------------------------------------------------------------------------------- collision meshes
# TR8 cdc Mesh (TRLAU-menu-hook level/Level.h, TR8 branch), 0x58 bytes:
#   BBox(2 x Vector3 16B) 0x00, position 0x20, m_vertices 0x30, m_faces 0x34, m_root (KD nodes) 0x38, clientData 0x3c,
#   u32 numNodes 0x40, numFaces 0x44, numVertices 0x48, numDegenerate 0x4c, numNonManifold 0x50, u16 vertexType 0x54, u16 height 0x56
# element layouts (verified on l2_norsehub): vertices float4 (type 1) or int16 x3 (type 0);
#   IndexedFace 20B = u32 i0,i1,i2, u8 adj, u8 coll, u16 clientFlags, u8 material + 3 bytes (raw on PC)
#   SignalFace  16B = u32 i0,i1,i2, u8, u8, u16 id ;   KD node 16B = float, float, u32, u8 + 3 bytes (raw)
FACE20 = ('s32', 's32', 's32', 'b2s16', 'raw')
FACE16 = ('s32', 's32', 's32', 'b2s16')
NODE16 = ('s32', 's32', 's32', 'raw')

def _ptrs(secs, e='be'):
    """{(sec, off): (target_sec, target_off)} for internal + external pointers of type-0 sections"""
    out = {}
    for s in secs:
        if s['type'] != 0 or not s['reloc']: continue
        r = R.parse(s['reloc'], e)
        for o, t in r.internal: out[s['i'], o] = (s['i'], t)
        for si, so, do in r.external: out[s['i'], so] = (si, do)
    return out

def mesh_overrides(secs, e='be'):
    """{(sec, word_off): class} for the vertex / face / KD-node arrays of every collision Mesh found in the DRM."""
    E = '>' if e == 'be' else '<'
    P = _ptrs(secs, e)
    ov = {}
    def region_end(si, t):
        return secs[si]['size']
    def put(si, t, n, stride, cls):
        d = secs[si]['size']
        for k in range(n):
            for j, c in enumerate(cls):
                o = t + k * stride + 4 * j
                if o + 4 <= d: ov[si, o] = c
    for (si, o), _ in P.items():
        m = o - 0x30
        if m < 0 or (si, m + 0x34) not in P or (si, m + 0x38) not in P: continue
        d = secs[si]['data']
        if d is None or m + 0x58 > len(d): continue
        nn, nf, nv = struct.unpack_from(E + '3I', d, m + 0x40)
        vt, = struct.unpack_from(E + 'H', d, m + 0x54)
        (vs, vo), (fs, fo), (ns, no) = P[si, m + 0x30], P[si, m + 0x34], P[si, m + 0x38]
        if secs[vs]['type'] != 0 or secs[fs]['type'] != 0 or secs[ns]['type'] != 0: continue
        if not (0 < nf < 1 << 24 and 0 < nv < 1 << 24 and nn < 1 << 24) or vt not in (0, 1): continue
        if len({(vs, vo), (fs, fo), (ns, no)}) != 3: continue
        fits = lambda s_, o_, n, st: (n * st - 4 <= secs[s_]['size'] - o_ <= n * st + 16) if o_ == 0 else (secs[s_]['size'] - o_ >= n * st - 4)
        fstride = 20 if fits(fs, fo, nf, 20) else 16 if fits(fs, fo, nf, 16) else None
        if fstride is None or not fits(ns, no, nn, 16) or not fits(vs, vo, nv, 16 if vt == 1 else 6): continue
        put(fs, fo, nf, fstride, FACE20 if fstride == 20 else FACE16)
        put(ns, no, nn, 16, NODE16)
        if vt == 1: put(vs, vo, nv, 16, ('s32',) * 4)
        elif vt == 0:
            for k in range(0, (6 * nv + 3) // 4): ov.setdefault((vs, vo + 4 * k), 's16') if (vo % 4 == 0) else None
    return ov

if __name__ == '__main__':
    from generic_cache import load_pairs
    import dlc_generic as DG
    P = load_pairs(); idm = idmaps(); ids = DG.DlcIds()
    for t, m in space_maps().items(): ids.base.setdefault(t, m)
    names = sorted(P)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'eval'
    if mode == 'save07':          # in-sample training only (fast): type0_table.pkl + type7_table.pkl (+ slim npz)
        T0 = train(P, names, idm, (0,)); pickle.dump(dict(T0.v), open(TABLE0, 'wb')); del T0
        T7 = train(P, names, idm, (7,)); pickle.dump(dict(T7.v), open(os.path.join(W, 'type7_table.pkl'), 'wb')); del T7
        mode = 'slim'
    if mode == 'slim':
        for n in ('type0_table', 'type7_table'):
            print(n, slim(os.path.join(W, n + '.pkl'), os.path.join(W, n + '_slim.npz')))
        sys.exit()
    if mode == 'quick7':          # fast held-out probe: train on 3/4 of the DRMs, test on every 4th; wrong-word sources
        A = [n for k, n in enumerate(names) if k % 4]; B = names[::4]
        TA = train(P, A, idm, (7,))
        st = evaluate(P, B, TA, ids, idm, types=(7,))
        report(st, 'TYPE 7 HELD-OUT probe (1/4 test)')
        for k, v in sorted(((k, v) for k, v in st.items() if isinstance(k, tuple) and k[0] == 'bad_src'), key=lambda kv: -kv[1])[:25]:
            print('   ', k[1:], v)
        sys.exit()
    if mode == 'eval7':           # same machinery for DTPData (type 7): held-out 2-fold + in-sample, table -> type7_table.pkl
        A = [n for n in names if zlib.crc32(n.encode()) & 1 == 0]
        B = [n for n in names if zlib.crc32(n.encode()) & 1 == 1]
        TA = train(P, A, idm, (7,)); TB = train(P, B, idm, (7,))
        st = evaluate(P, B, TA, ids, idm, types=(7,)); st.update(evaluate(P, A, TB, ids, idm, types=(7,)))
        report(st, 'TYPE 7 HELD-OUT 2-fold by DRM name')
        sys.exit()                # tables are written only by 'save07' (evaluations never race a running conversion)
    if mode == 'eval':
        A = [n for n in names if zlib.crc32(n.encode()) & 1 == 0]
        B = [n for n in names if zlib.crc32(n.encode()) & 1 == 1]
        TA = train(P, A, idm); TB = train(P, B, idm)
        st = evaluate(P, B, TA, ids, idm); st.update(evaluate(P, A, TB, ids, idm))
        report(st, 'HELD-OUT 2-fold by DRM name (type-0 table only)')
        sys.exit()
    if mode == 'quick':
        det = []
        report(evaluate(P, names, table0(), ids, idm, detail=det), 'IN-SAMPLE (saved table)')
        pickle.dump(det, open(os.path.join(W, 'type0_bad.pkl'), 'wb'))
        sys.exit()
    print('modes: save07 | slim | eval | eval7 | quick')

