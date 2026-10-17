"""Global unit-level id spaces that are numbered differently on PC (found 2026-10-08, see NOTES.md):
  unit   : StreamUnitID = 1-based record index of the unit in objlist.dat (verified 82/82 units both platforms).
           Level+0x4c (u32), StreamUnitPortal+0x84 (u16 destination unit), planner/area structs (u16).
  portal : global portal/signal numbering (u16): Level+0x94 u16[numPortals] (own portal ids),
           StreamUnitPortal+0x80 (u16 id of the matching portal in the destination unit), +0x82 (own id).
           Xbox numbers levels in build order l1,l5,l6,l7,l2,l3,l4; PC in l1..l7 order.
  tguid  : TerrainGroup.uniqueID (u32 @ +0x28 of the 0x50-byte TerrainGroup), global numbering.
  intro  : Intro.uniqueID (u32 @ +0x58 of the 0x90-byte Intro records in the unit DTP Level+0x74 -> {.., u32 n @0xc, Intro* @0x10}),
           global numbering in level blocks (e.g. +4826 / -2709 ...); referenced from scripts (native init blocks) and DTPs.
  object : Intro +0x50 u16 objectID (objlist object id; mapped with the name-based object remap, type 11).
Unit DRM detection: section 0 = Level whose u32 @0 is an external pointer to a 24-byte Terrain section
  {s16 0, s16 numPortals, StreamUnitPortal* (into Level+0xa0, 0x100 stride, name[128] first), int numTG, TG*, signalTG*}.
build() -> work/generic/unit_idmaps.json {space: {xbox: pc}} from the base pairs (+ objlist names for 'unit').
"""
import sys, os, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
OUT = os.path.join(W, 'unit_idmaps.json')

def level_info(secs, e='be'):
    """secs: parsed DRM sections (dicts with data/reloc/size). Returns dict or None if not a unit DRM."""
    if not secs or secs[0]['type'] != 0 or secs[0]['data'] is None: return None
    rx = R.parse(secs[0]['reloc'], e)
    ext = {so: (si, do) for si, so, do in rx.external}
    if 0 not in ext: return None
    ti, _ = ext[0]
    if secs[ti]['size'] != 24 or secs[ti]['data'] is None: return None
    E = '>' if e == 'be' else '<'
    td = secs[ti]['data']
    rt = R.parse(secs[ti]['reloc'], e); text = {so: (si, do) for si, so, do in rt.external}
    npor = struct.unpack_from(E + 'h', td, 2)[0]; ntg = struct.unpack_from(E + 'i', td, 8)[0]
    portals = []
    if 4 in text:
        si, do = text[4]
        portals = [(si, do + 0x100 * k) for k in range(npor)]
    tgs = []
    if 0xc in text:
        si, do = text[0xc]; tgs += [(si, do + 0x50 * k) for k in range(ntg)]
    if 0x10 in text:
        si, do = text[0x10]; tgs.append((si, do))
    intros = []; recs = []; dportals = []; nodes = []   # unit DTP (Level+0x74): {u32, ptr, ptr, u32 numIntros @0xc, Intro* @0x10, ..}
    if 0x74 in ext:
        di, do = ext[0x74]
        s = secs[di]
        if s['type'] == 7 and s['data'] is not None and do == 0 and len(s['data']) >= 0x14:
            ri = dict(R.parse(s['reloc'], e).internal)
            n = struct.unpack_from(E + 'I', s['data'], 0xc)[0]
            t = ri.get(0x10)
            if t is not None and t + 0x90 * n <= len(s['data']):
                intros = [(di, t + 0x90 * k) for k in range(n)]
            if len(s['data']) >= 0xa0:      # +0x98 numPortals, +0x9c -> 0x40-byte portal records, u16 portal id @+8
                n3 = struct.unpack_from(E + 'I', s['data'], 0x98)[0]; t3 = ri.get(0x9c)
                if t3 is not None and 0 < n3 < 64 and t3 + 0x40 * n3 <= len(s['data']):
                    dportals = [(di, t3 + 0x40 * k) for k in range(n3)]
            if len(s['data']) >= 0xb8:      # +0xac n, +0xb4 -> 0x40-byte records {pos, rot, u32 global id @+0x20, ...}
                n4 = struct.unpack_from(E + 'I', s['data'], 0xac)[0]; t4 = ri.get(0xb4)
                if t4 is not None and 0 < n4 < 100000 and t4 + 0x40 * n4 <= len(s['data']):
                    nodes = [(di, t4 + 0x40 * k) for k in range(n4)]
            n2 = struct.unpack_from(E + 'I', s['data'], 0x2c)[0] if len(s['data']) >= 0x38 else 0
            t2 = ri.get(0x34)
            if t2 is not None and 0 < n2 < 10000 and t2 + 0xb0 * n2 <= len(s['data']):
                recs = [(di, t2 + 0xb0 * k) for k in range(n2)]
    return dict(terrain=ti, npor=npor, portals=portals, tgs=tgs, intros=intros, recs=recs, dportals=dportals, nodes=nodes)

def unit_fields(secs, e='be'):
    """[(sec_index, offset, width('u16'|'u32'), space)] of the known id fields of a unit DRM."""
    L = level_info(secs, e)
    if L is None: return []
    f = [(0, 0x4c, 'u32', 'unit')]
    f += [(0, 0x94 + 2 * k, 'u16', 'portal') for k in range(L['npor'])]
    for si, o in L['portals']:
        f += [(si, o + 0x80, 'u16', 'portal'), (si, o + 0x82, 'u16', 'portal'), (si, o + 0x84, 'u16', 'unit')]
    for si, o in L['tgs']:
        f.append((si, o + 0x28, 'u32', 'tguid'))
    for si, o in L['intros']:       # Intro (0x90 B): +0x50 u16 objectID (objlist id), +0x58 u32 uniqueID (global)
        f += [(si, o + 0x50, 'u16', 'object'), (si, o + 0x58, 'u32', 'intro')]
    for si, o in L['nodes']:        # unit DTP +0xac n, +0xb4 -> 0x40-byte records, u32 unique id @+0x20 = SAME global space
        f.append((si, o + 0x20, 'u32', 'intro_n'))  # as Intro.uniqueID (disjoint keys, 0 conflicts; scripts reference both)
    for si, o in L['dportals']:     # unit DTP portal records (engine lookup table keyed by portal id; crash 0x5c6cf1)
        f.append((si, o + 8, 'u16', 'portal'))
    for si, o in L['recs']:         # unit DTP +0x2c n, +0x34 -> 0xb0-byte records, u16 global id @+0x48 (level blocks,
        f.append((si, o + 0x48, 'u16', 'rec'))   # Xbox-608 / +1084 ...; also u32 in Script init blocks of userType Symbol 94)
    return f

def read(d, o, w, e):
    E = '>' if e == 'be' else '<'
    return struct.unpack_from(E + ('H' if w == 'u16' else 'I'), d, o)[0]

def objlist_unit_ids(path, e):
    import objlists as O
    recs, _ = O.read_objlist(open(path, 'rb').read(), e)
    return {nm.split('\\')[-1]: k + 1 for k, (nm, _) in enumerate(recs)}

def build():
    from generic_cache import load_pairs
    P = load_pairs()
    v = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for nm, ((xh, sx), (ph, sp)) in P.items():
        fx = unit_fields(sx, 'be'); fp = unit_fields(sp, 'le')
        if not fx: continue
        zz = []
        for spc in set(f[3] for f in fx):
            a = [f for f in fx if f[3] == spc]; b = [f for f in fp if f[3] == spc]
            if len(a) == len(b): zz += list(zip(a, b))
        for (si, o, w, sp_), (pi, po, pw, _) in zz:
            if sx[si]['data'] is None or sp[pi]['data'] is None: continue
            v[sp_][read(sx[si]['data'], o, w, 'be')][read(sp[pi]['data'], po, pw, 'le')] += 1
    L = os.path.join(W, 'lists')
    xu = objlist_unit_ids(os.path.join(L, 'xboxtu_objlist.dat'), 'be')
    pu = objlist_unit_ids(os.path.join(W, 'merged', 'tr8', 'pc-w', 'objlist.dat'), 'le')
    out = {}; st = {}
    v.pop('object', None)
    for x, c in v.pop('intro_n', {}).items(): v['intro'][x].update(c)     # node ids share the intro unique-id space
    for sp_, d in v.items():
        m = {}; bad = 0
        for x, c in d.items():
            (p, n), = c.most_common(1); m[x] = p; bad += n != sum(c.values())
        inv = collections.Counter(m.values())
        st[sp_] = dict(n=len(m), contested=bad, non_injective=sum(1 for k, n in inv.items() if n > 1))
        out[sp_] = m
    # intro ids referenced from Script native init blocks (DataType userType Symbol 50: u32, 4261: u16 in the first half)
    # that no unit DTP pair covers: add their votes (only where consistent and injective)
    try:
        import pickle, script_conv as S
        L = pickle.load(open(os.path.join(W, '..', 'script', 'pairs_8.pkl'), 'rb'))
        iv = collections.defaultdict(collections.Counter)
        for r in L:
            rel = R.parse(r['xr'], 'be'); Wk = S.walk(r['xd'], rel)
            skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            for w, lab in Wk.lab.items():
                if w in skip: continue
                if lab[0] == 'init' and len(lab) == 5 and lab[4] in (50, 4261):
                    if lab[4] == 50: x, p_ = struct.unpack_from('>I', r['xd'], w)[0], struct.unpack_from('<I', r['pd'], w)[0]
                    else: x, p_ = struct.unpack_from('>H', r['xd'], w)[0], struct.unpack_from('<H', r['pd'], w)[0]
                    if x not in (0, 0xffff, 0xffffffff): iv[x][p_] += 1
        im = out['intro']; used = set(im.values()); add = 0; conflict = 0
        for x, c in iv.items():
            (p_, n), = c.most_common(1)
            if x in im: conflict += im[x] != p_; continue
            if n == sum(c.values()) and p_ not in used: im[x] = p_; used.add(p_); add += 1
        st['intro_from_scripts'] = dict(added=add, disagree_with_units=conflict)
    except Exception as e:
        st['intro_from_scripts'] = repr(e)
    # unit ids: name based (covers DLC units too); check against the pair evidence
    um = {xu[n]: pu[n] for n in xu if n in pu}
    st['unit_vs_objlist'] = dict(agree=sum(1 for x, p in out.get('unit', {}).items() if um.get(x) == p),
                                 disagree=[(x, p, um.get(x)) for x, p in out.get('unit', {}).items() if um.get(x) != p][:10])
    out['unit'] = um
    json.dump({k: {str(a): b for a, b in sorted(m.items())} for k, m in out.items()}, open(OUT, 'w'))
    return out, st

if __name__ == '__main__':
    out, st = build()
    print(json.dumps(st, indent=1))
    for k, m in out.items(): print(k, len(m), 'xbox max', max(m), 'pc max', max(m.values()))
