"""DLC (Xbox) -> PC conversion of the generic part of a DRM: ids, generic sections, assembly.

DlcIds(t, xid) -> PC id      (one deterministic table for every agent: work/generic/dlc_idmap.json)
  t == 11 (object ids)  : name-based object remap (objlists.py; base objects -> PC id, 822..1045 identity)
  t == 100 (Symbols u16): base map (generic_symbols) ; else consistent-span interpolation ; else
                          Xbox ids above the Xbox base maximum are shifted by (PC max - Xbox max) ;
                          remaining unmapped base-range symbols use the nearest lower neighbour's offset
  other types           : base id map (generic_ids, Xbox<->PC pairs incl. patch.000/TitleUpdate) ;
                          DLC-new ids keep their Xbox value unless it collides with any PC section id of
                          that type (or a mapped PC id), in which case they get max(...)+1, +2, ...

convert_drm(xsecs, ...) -> (drm_write.Drm, report) converts every section, routes:
  A 'pc_copy'   generic section whose Xbox id is a base id AND whose content is identical to the Xbox
                base content -> PC section bytes copied (external reloc section indices re-targeted)
  B 'template'  base id, same size + same reloc layout as the Xbox base version, content edited:
                start from the PC base section, re-convert only the words that differ on Xbox
  C 'convert'   Anim/Obj exact converters, otherwise learned word masks (generic_learn)
  media types (5,6,9,10,12) are delegated to the callback media(t, xsec, new_id, ids) -> (data, reloc)
  or passed through unconverted when no callback (flagged 'media_passthrough').
"""
import sys, os, json, struct, bisect, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
import convert_generic as CG
from generic_store import norm_hash
import drm_write as DW
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
GENERIC = (0, 2, 7, 8, 11, 13)
MEDIA = (5, 6, 9, 10, 12)
SYM = G.SYM
LOC = 101          # pseudo type: localisation string index (locals.bin), see tools/locals.py

class DlcIds:
    def __init__(self, store=None, dlc=None, table_path=os.path.join(W, 'dlc_idmap.json'), rebuild=False):
        raw = json.load(open(os.path.join(W, 'idmap.json')))
        self.base = {int(t): {int(a): b for a, b in d.items()} for t, d in raw.items()}
        obj = json.load(open(os.path.join(W, 'merged', 'object_id_remap_xbox_to_pc.json')))
        self.base[11] = {int(a): b for a, b in obj.items()}
        self._sym_setup()
        try:        # unit-level global id spaces (generic_type0 / unit_ids): 110 unit, 111 portal, 112 terrain-group uid
            import generic_type0
            for t, m in generic_type0.space_maps().items(): self.base.setdefault(t, m)
        except Exception:
            pass
        self.missing = collections.Counter()
        self._loc = None
        if os.path.exists(table_path) and not rebuild:
            d = json.load(open(table_path))
            self.new = {int(t): {int(a): b for a, b in v.items()} for t, v in d['new'].items()}
        else:
            self.new = self.build_new(store, dlc)
            json.dump({'rule': __doc__.split('\n\n')[1], 'new': {str(t): {str(a): b for a, b in sorted(v.items())} for t, v in self.new.items()},
                       'sym_info': self.sym_info}, open(table_path, 'w'))

    PC_SYM_MAX = 16828       # largest PC symbol seen anywhere (patch.000 generalbank script names)

    def _sym_setup(self):
        m = self.base.get(SYM, {})
        self.sks = sorted(m)
        self.sused = set(m.values())
        self.xs_max = max(m); self.ps_max = max(max(m.values()), self.PC_SYM_MAX)
        self.sym_info = dict(mapped=len(m), xbox_max=self.xs_max, pc_max=self.ps_max, shift=self.ps_max - self.xs_max,
                             collision_base=40000)
        self.sym_stats = collections.Counter()

    def sym(self, xs):
        """Xbox Symbol -> PC Symbol. Unmapped DLC-new symbols (> Xbox base max) go above the PC max (shift);
        unmapped base-range ones inside a consistent span are interpolated (exact in leave-one-out), otherwise
        guessed from the lower neighbour's offset; a guess that would hit an existing PC symbol -> 40000+xs."""
        m = self.base[SYM]
        if xs in m: self.sym_stats['mapped'] += 1; return m[xs]
        if xs == 0 or xs == 0xffff: self.sym_stats['null'] += 1; return xs
        if xs > self.xs_max: self.sym_stats['dlc_new_shift'] += 1; return xs + self.ps_max - self.xs_max
        k = bisect.bisect_left(self.sks, xs)
        if 0 < k < len(self.sks):
            a, b = self.sks[k - 1], self.sks[k]
            if m[b] - m[a] == b - a: self.sym_stats['interpolated'] += 1; return m[a] + xs - a
            g = m[a] + xs - a
            if g not in self.sused: self.sym_stats['guess_lower'] += 1; return g
            self.sym_stats['guess_collision_new'] += 1; return 40000 + xs
        self.sym_stats['identity_below_min'] += 1
        return xs

    def extend(self, store, want, path=os.path.join(W, 'dlc_idmap.json')):
        """Add new-id entries for {type: set(xid)} not yet covered (base map or table); existing entries never
        change (files already converted keep their ids). Same rule: identity unless taken, else max+1."""
        pc_ids = store['pc_ids']; added = collections.Counter()
        for t, xs in sorted(want.items()):
            if t in (11, SYM): continue
            bm = self.base.get(t, {}); nd = self.new.setdefault(t, {})
            todo = sorted(x for x in xs if x not in bm and x not in nd)
            if not todo: continue
            taken = set(pc_ids.get(t, ())) | set(bm.values()) | set(nd.values())
            nxt = max(taken | set(todo) | set(nd) | {0}) + 1
            for x in todo:
                if x not in taken: nd[x] = x
                else: nd[x] = nxt; nxt += 1
                taken.add(nd[x]); added[t] += 1
        d = json.load(open(path)) if os.path.exists(path) else {'rule': __doc__.split('\n\n')[1]}
        d['new'] = {str(t): {str(a): b for a, b in sorted(v.items())} for t, v in self.new.items()}
        d['sym_info'] = self.sym_info
        json.dump(d, open(path, 'w'))
        return added

    def build_new(self, store, dlc):
        """dlc: {key: (hdr, secs)} Xbox DLC DRMs; store: generic_store.load()"""
        pc_ids = store['pc_ids']
        want = collections.defaultdict(set)
        for k, (h, secs) in dlc.items():
            for s in secs:
                want[s['type']].add(s['id'])
                if s['reloc'] and s['data'] is not None:
                    r = R.parse(s['reloc'], 'be')
                    for t, o in r.idref + r.idref_a:
                        if o + 4 <= len(s['data']):
                            v, = struct.unpack_from('>I', s['data'], o)
                            if v not in (0, 0xffffffff): want[t].add(v)
        new = {}
        for t, xs in sorted(want.items()):
            if t == 11: continue
            bm = self.base.get(t, {})
            taken = set(pc_ids.get(t, ())) | set(bm.values())
            todo = sorted(x for x in xs if x not in bm)
            nxt = max(taken | set(todo) | {0}) + 1
            d = {}
            for x in todo:
                if x not in taken: d[x] = x
                else: d[x] = nxt; nxt += 1
                taken.add(d[x])
            new[t] = d
        return new

    local = {}      # per-DRM overrides {(type, xbox_id): pc_id}, set by convert_drm to keep ids unique inside one DRM

    def loc(self, x):
        """Xbox (TU) localisation string index -> PC string id (tools/locals.py build; 0 = null). Unknown -> x."""
        if self._loc is None:
            p = os.path.join(W, 'locals', 'locmap_xbox_to_pc.json')
            self._loc = {int(k): v for k, v in json.load(open(p))['map'].items()} if os.path.exists(p) else {}
        if x in self._loc: return self._loc[x]
        self.missing[LOC] += 1
        return x

    def __call__(self, t, xid):
        if t == SYM: return self.sym(xid)
        if t == LOC: return self.loc(xid)
        lo = self.local.get((t, xid))
        if lo is not None: return lo
        b = self.base.get(t)
        if b is not None and xid in b: return b[xid]
        n = self.new.get(t)
        if n is not None and xid in n: return n[xid]
        if t == 113 and b and _G0() is not None:   # DLC-new intro uniqueID colliding with a PC intro id -> fresh id
            return _G0().intro_new(b, xid)
        self.missing[t] += 1
        return xid

# ------------------------------------------------------------------------------------------------
_T = None
class _SlimTable:
    """best-class lookup from the compact numpy index (tools/slim2np.py)."""
    def __init__(self, h, c, vocab):
        self.h, self.c, self.vocab = h, c, vocab
    def best(self, key):
        import hashlib, numpy as np
        hv = np.uint64(int.from_bytes(hashlib.blake2b(repr(key).encode(), digest_size=8).digest(), 'little'))
        i = int(np.searchsorted(self.h, hv))
        if i < len(self.h) and self.h[i] == hv:
            return self.vocab[int(self.c[i])]
        return None

def table():
    global _T
    if _T is None:
        npz = os.path.join(W, 'mask_best.npz')
        if os.path.exists(npz):
            import numpy as np
            z = np.load(npz)
            _T = _SlimTable(z['h'], z['c'], pickle.load(open(os.path.join(W, 'mask_best_vocab.pkl'), 'rb')))
        else:
            v, n = pickle.load(open(os.path.join(W, 'mask_table.pkl'), 'rb'))
            _T = G.Table(); _T.v.update(v); _T.n.update(n)
    return _T

def retarget_ext(reloc_le, ext_targets, index_of):
    """PC reloc blob whose external entries point at (type,id) targets -> blob for the new DRM layout."""
    r = R.parse(reloc_le, 'le')
    out = []
    for (si, so, do), tgt in zip(r.external, ext_targets):
        j = index_of.get(tgt)
        if j is None: return None
        out.append((j, so, do))
    r.external = out
    return R.write(r, 'le')

def template_convert(xd, xbase, pcbase, rel, regions, T, ids):
    """PC base section + Xbox edit: words equal to the Xbox base keep the PC bytes; changed words are
    converted with the class seen for that word in the (Xbox base -> PC base) pair, else learned class."""
    out = bytearray(pcbase)
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    n4 = len(xd) // 4 * 4
    for w, key, ck in G.word_keys(len(xd), regions):
        if w in skip or xd[w:w + 4] == xbase[w:w + 4]: continue
        cs = G.word_classes(xbase[w:w + 4], pcbase[w:w + 4], ids.base) or []
        c, _ = G.lookup(T, key, ck)
        if cs and c not in cs:
            c = sorted(cs, key=lambda k: G.PREF.get(k, 9))[0]
        if c is None:
            c = 'raw' if G.is_text(xd[w:w + 4]) else 's32'
        out[w:w + 4] = G.apply_word(xd[w:w + 4], c, ids)
    if len(xd) > n4 and xd[n4:] != xbase[n4:]: out[n4:] = xd[n4:]
    for o in rel.pointer_offsets(): out[o:o + 4] = xd[o:o + 4][::-1]
    for o, t in rel.id_offsets().items():
        v, = struct.unpack_from('>I', xd, o)
        struct.pack_into('<I', out, o, ids(t, v) if v not in (0, 0xffffffff) else v)
    return bytes(out)

_SLm = None
def _SL():
    """script_learn module with its table loaded (work/script/script_table.pkl), None if unavailable"""
    global _SLm
    if _SLm is None:
        try:
            import script_learn
            script_learn.table()
            _SLm = script_learn
        except Exception:
            _SLm = False
    return _SLm or None

_G0m = None
def _G0():
    """generic_type0 module (type-0 table + unit id spaces), None if unavailable"""
    global _G0m
    if _G0m is None:
        try:
            import generic_type0
            _G0m = generic_type0
        except Exception:
            _G0m = False
    return _G0m or None

_PCV = None
def pc_vers():
    """{'type:pcid': ver} of the PC sections (most frequent; patch.000 wins) - work/generic/pc_vers.json"""
    global _PCV
    if _PCV is None:
        p = os.path.join(W, 'pc_vers.json')
        _PCV = json.load(open(p)) if os.path.exists(p) else {}
    return _PCV

_PCVC = None
def pc_vers_content():
    """{'type:pcid:md5(data)[:16]': ver} for PC Script/DTP sections (work/generic/pc_vers_content.json)"""
    global _PCVC
    if _PCVC is None:
        p = os.path.join(W, 'pc_vers_content.json')
        _PCVC = json.load(open(p)) if os.path.exists(p) else {}
    return _PCVC

XLATE_STATS = collections.Counter()
_REAUTH = None
def _layout(blob, e):
    r = R.parse(blob, e)
    return (r.internal, [(so, do) for _, so, do in r.external], r.idref, r.idref_a)

def reauthored(store, ids):
    """{(type, xbox id): pc id} of base Scripts (67) / DTPs whose PC version has a DIFFERENT layout (size, internal relocs;
    for DTP also the external/id-ref layout) = PC re-authored."""
    global _REAUTH
    if _REAUTH is None:
        _REAUTH = {}
        for (t, x), xb in store['xb_store'].items():
            if t not in (7, 8): continue
            p = ids.base.get(t, {}).get(x); pc = store['pc_store'].get((t, p))
            if pc is None: continue
            if len(pc['data']) != len(xb['data']):
                _REAUTH[t, x] = p; continue
            if t == 8 and (R.parse(pc['reloc'], 'le').internal != R.parse(xb['reloc'], 'be').internal or str(x) in _script_differs()):
                _REAUTH[t, x] = p
            elif t == 7 and (_layout(pc['reloc'], 'le') != _layout(xb['reloc'], 'be') or str(x) in _dtp_differs()):
                _REAUTH[t, x] = p
    return _REAUTH

def _script_differs():
    """Xbox script ids whose PC content has a word no conversion class reproduces (work/generic/script_pc_differs.json)"""
    p = os.path.join(W, 'script_pc_differs.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def _dtp_differs():
    """Xbox DTP ids whose PC content has >= 4 words no conversion class reproduces (work/generic/dtp_pc_differs.json, 97)"""
    p = os.path.join(W, 'dtp_pc_differs.json')
    return json.load(open(p)) if os.path.exists(p) else {}

_XL = {}
def xlate_map(store, ids, x):
    """Xbox-layout offset -> PC-layout offset inside re-authored base script x (script_conv.offset_map; validated on the
    base pairs: 5344 ok / 1 wrong / 8 unmapped external-reloc targets)."""
    if x not in _XL:
        import script_conv as SC, pickle as _pk
        if x[0] == 7:       # DTP: no typed walker; offset 0 + evidence from base pairs (work/script/ext_xlate.json)
            xp = os.path.join(W, '..', 'script', 'ext_xlate.json')
            ev = json.load(open(xp)).get('7:%d' % x[1], {}) if os.path.exists(xp) else {}
            _XL[x] = {0: 0}; _XL[x].update({int(a): b for a, b in ev.items()})
            return _XL[x]
        xb = store['xb_store'][x]; pc = store['pc_store'][x[0], reauthored(store, ids)[x]]
        vp = os.path.join(W, '..', 'script', 'symvotes.pkl')
        sm = {a: c.most_common(1)[0][0] for a, c in _pk.load(open(vp, 'rb')).items()} if os.path.exists(vp) else ids.base.get(SYM, {})
        _XL[x] = SC.offset_map(xb['data'], R.parse(xb['reloc'], 'be'), pc['data'], R.parse(pc['reloc'], 'le'), sm)
    return _XL[x]

_AIDX = None
ANALOG_STATS = collections.Counter()
MODEL_STATS = collections.Counter()
def _reloc_sig(blob, e):
    r = R.parse(blob, e)
    return hash((tuple(r.internal), tuple((so, do) for _, so, do in r.external), tuple(r.idref), tuple(r.idref_a)))

def analog_index(store, ids):
    """{(type, size, Xbox reloc layout): [xbox base id]} of base DTPs that have a PC counterpart (analog search)."""
    global _AIDX
    if _AIDX is None:
        _AIDX = collections.defaultdict(list)
        for (t, x), xb in store['xb_store'].items():
            if t != 7: continue
            p = ids.base.get(t, {}).get(x)
            if p is None or (t, p) not in store['pc_store']: continue
            _AIDX[t, len(xb['data']), _reloc_sig(xb['reloc'], 'be')].append(x)
    return _AIDX

ANALOG_MAX_DIFF = 64
def analog_convert(s, xsecs, ids, store, exclude=()):
    """DLC-new DTP that is a near-clone of a base Xbox DTP (same size + reloc layout, <= ANALOG_MAX_DIFF differing words, all
    of them section-id-like values) -> build it from the PC version of that base DTP (which may be PC RE-AUTHORED, i.e. have
    another size/layout: e.g. the Lara costume DTPs, Xbox 164732/549808 B vs PC 164988/550112 B). Differing words are placed
    by occurrence alignment (k-th occurrence of the analog's Xbox value <-> k-th occurrence of its PC value), id-ref fields by
    reloc order. Returns (data, reloc_le, analog_xid) or None (no analog / not provable -> caller falls back)."""
    import numpy as np
    t, xd = s['type'], s['data']
    if t != 7 or len(xd) < 8: return None
    cands = [x for x in analog_index(store, ids).get((t, len(xd), _reloc_sig(s['reloc'], 'be')), ()) if x not in exclude]
    if not cands: return None
    n = len(xd) // 4
    xw = np.frombuffer(xd, '>u4', n)
    ranked = sorted((int(np.count_nonzero(np.frombuffer(store['xb_store'][t, x]['data'], '>u4', n) != xw)), x) for x in cands)
    rx = R.parse(s['reloc'], 'be')
    have = collections.defaultdict(set)
    for q in xsecs: have[q['type']].add(q['id'])
    near = [x for d, x in ranked if d <= ANALOG_MAX_DIFF]
    if len({len(store['pc_store'][t, ids.base[t][x]]['data']) for x in near}) > 1:
        ANALOG_STATS['pc_disagree'] += 1; return None    # PC re-authoring is per id, not per content: need consensus
    why = 'too_different'
    for nd, ax in ranked[:ANALOG_TRIES]:          # several analogs tie (all Lara costumes); some PC versions do not align
        if nd > ANALOG_MAX_DIFF: break
        if len(xd) % 4 and xd[n * 4:] != store['xb_store'][t, ax]['data'][n * 4:]: continue
        r = _analog_build(xd, xw, rx, ax, n, ids, store, have)
        if isinstance(r, str): why = r; continue
        ANALOG_STATS['ok'] += 1
        return r[0], r[1], ax
    ANALOG_STATS[why] += 1
    return None

MODEL_MAGIC = bytes.fromhex('04c20453')       # first word of 1057 base 'model' DTPs (segment/HInfo skeleton data)
MODEL_HDR_U32 = (0, 4, 16, 20, 24, 28, 32, 40, 48, 56, 64, 68, 84, 92)
MODEL_HDR_U16 = (104, 108, 112)
MODEL_HINFO_U32 = (0, 8, 16, 24, 32)        # counts of the 5 {u32 n, ptr} pairs (spheres, ..): the n*stride of the alloc
def model_fix(xd, rel, out):
    """Typed override for model DTPs (Xbox word0 0x04c20453): header {.., u32 nseg @4, ptr seg[] @0xc}, segments 0x40 B
    (all u32 except u16 pair @+0x34, HInfo* @+0x3c), HInfo {u32 n, ptr} x5.  Field classes learned on the 1055 base pairs
    (every listed field: 100% u32 resp. u16-pair).  The learned type-7 table left 2 of 11 HInfo counts of the DLC object
    ma_ani_adren_trap raw (BE 1 -> 0x01000000) -> 8*(sum+2n) = 0x10000078 = the 256 MB 'Out of memory' (0x5b3230).
    Returns the number of words changed."""
    if xd[:4] != MODEL_MAGIC or len(xd) < 0x80: return 0
    it = dict(rel.internal); ptrs = set(rel.pointer_offsets()) | set(rel.id_offsets())
    tg = sorted(set(it.values()) | {len(xd)})
    ch = [0]
    def put(o, u16=False):
        if o in ptrs or o + 4 > len(xd): return
        w = xd[o:o + 4]
        v = (w[1::-1] + w[:1:-1]) if u16 else w[::-1]
        if out[o:o + 4] != v: out[o:o + 4] = v; ch[0] += 1
    for o in MODEL_HDR_U32: put(o)
    for o in MODEL_HDR_U16: put(o, True)
    seg = it.get(0xc); n = struct.unpack_from('>I', xd, 4)[0]
    if seg is None or seg + 0x40 * n > len(xd): return ch[0]
    for j in range(n):
        e = seg + 0x40 * j
        for k in range(0, 0x3c, 4): put(e + k, k == 0x34)
        h = it.get(e + 0x3c)
        if h is not None and h + 0x28 <= len(xd):
            for k in MODEL_HINFO_U32: put(h + k)
            for k, (es, fl) in MODEL_HARR.items():      # HInfo element arrays: only fields 100% one class on base pairs
                c = struct.unpack_from('>I', xd, h + 8 * k)[0]; a = it.get(h + 8 * k + 4)
                if not c or a is None: continue
                nx = min([v for v in tg if v > a], default=len(xd))
                if nx - a != es * c: continue                # element size not provable -> leave to the table
                for q in range(c):
                    for off, u16 in fl: put(a + q * es + off, u16)
    return ch[0]
MODEL_HARR = {0: (36, ((16, False),)), 1: (68, ((0, False), (4, False), (8, False), (44, False))), 2: (32, ((4, True),)),
              3: (56, ((40, True),))}

SCRIPT_REBASE_OPS = (0x0c, 0x0f, 0x10)      # bytecode ops whose 24-bit operand is an offset into the instance
REBASE_STATS = collections.Counter()
def script_layout_shift(sup, xsecs, store, ids):
    """[(xbox boundary, delta)] for a script class whose super is Xbox id `sup`: every BASE ancestor whose PC instance size
    (root u16 @+0x1c) differs from Xbox (PC re-authored classes grew, e.g. 2843 0x34->0x40, 2840/16787 0x6c->0x78) gives
    (its Xbox size, PC-Xbox size). DLC-new ancestors (found in xsecs) are walked through.  None = chain not resolvable."""
    loc = {q['id']: q for q in xsecs if q['type'] == 8}
    out = []; seen = set()
    while sup and sup not in seen:
        seen.add(sup)
        xb = store['xb_store'].get((8, sup))
        if xb is not None:
            pc = store['pc_store'].get((8, ids.base.get(8, {}).get(sup)))
            if pc is None: return None
            xs = struct.unpack_from('>H', xb['data'], 0x1c)[0]; ps = struct.unpack_from('<H', pc['data'], 0x1c)[0]
            if ps != xs: out.append((xs, ps - xs))
            sup = struct.unpack_from('>I', xb['data'], 0x18)[0]
        elif sup in loc and len(loc[sup]['data']) >= 0x20:
            sup = struct.unpack_from('>I', loc[sup]['data'], 0x18)[0]
        else:
            return None
    return sorted(out)

def script_rebase(xd, rel, out, shifts, W=None):
    """Shift instance offsets of a converted Script whose ancestors grew on PC: root size, own DataMember offsets, StartFunction
    offsets and member-access operands (ops 0x0c/0x0f/0x10) >= the growth boundary.  Rule learned + validated on the 116 base
    scripts whose super chain has a size delta (tools/script_rebase_validate.py).  Returns #words changed."""
    if not shifts: return 0
    import script_conv as S
    W = W or S.walk(xd, rel)
    def f(o):
        d = 0
        for b, dl in shifts:
            if o >= b: d = dl
        return o + d
    n = 0
    for w, lab in W.lab.items():
        if w + 4 > len(out): continue
        v = struct.unpack_from('<I', out, w)[0]
        if w == 0x1c and lab[:1] == ('root',):
            nv = (v & 0xffff0000) | (f(v & 0xffff) & 0xffff)
        elif lab[:2] == ('dm.off', 'member'):
            nv = (v & 0xffff0000) | (f(v & 0xffff) & 0xffff)
        elif lab[:2] == ('sfi', 4):
            nv = f(v)
        elif lab[0] == 'code.op' and len(lab) > 1 and lab[1] in SCRIPT_REBASE_OPS:
            nv = (v & 0xff000000) | (f(v & 0xffffff) & 0xffffff)
        else:
            continue
        if nv != v: struct.pack_into('<I', out, w, nv); n += 1
    return n

# dlc_level1_start script 20068 (state 0 Run): after '=== DLC Title Update has been found! ===' it waits in state 0 until the
# loading screen broadcasts a message; its OnMessage handler then does 'push 1; op 0x7d' = gotostate 1 (state-1 Run plays
# cine_dlc1_start_spangs). Only the Xbox TU uiloading (generalbank script 6) sends that message; the PC script 6 is pre-TU and
# replacing it crashes the base game (gb1.dmp). Patch: the two line-marker no-ops right after the 'found' print become
# 'push 1; gotostate' (op 0x7d with a pushed constant < #states: 382/382 uses in the base scripts).
CINE_NOWAIT = {20068: dict(at=0x250, xbox=bytes.fromhex('0000000e' '0000000f' '7b000000'), handler=(0x394, bytes.fromhex('04000001' '7d000000')))}
def cine_nowait(xid, xd, out):
    """returns True if patched (out: bytearray of the converted LE Script)"""
    c = CINE_NOWAIT.get(xid)
    if c is None or len(out) != len(xd): return False
    a, h = c['at'], c['handler']
    if xd[a:a + 12] != c['xbox'] or xd[h[0]:h[0] + 8] != h[1] or b'=== DLC Title Update has been found! ===' not in xd: return False
    out[a:a + 8] = struct.pack('<II', 0x04000001, 0x7d000000)
    return True

# Skip the dlc_level1_start intro cinematic (user decision 2026-10-09: the cine never reaches ReadyToPlay on PC yet).
# 20068 state-1 Run: 'get cine object (instanceref member 0x18), cast to class 23175, op 0x6a virtual call' through
# Prototype 941@9232 (vtIndex 57 = PlayCinematic). Retarget that call to 23175's own Prototype @1528 (vtIndex 61, the
# handler that prints 'warping lara to dlc_caverns checkpoint90001' and does gotostate 3 = state-3 Run: the warp).
CINE_SKIP = {20068: dict(src=0x6c4, xb_target=(8, 941, 9232), new_target=(8, 23175, 1528), proto_vt=0x3d)}
def cine_skip_reloc(xid, xsecs, reloc_le, k_of):
    """returns the patched LE reloc blob or None. k_of(type, xbox id) -> section index in the output DRM"""
    c = CINE_SKIP.get(xid)
    if c is None: return None
    xs = next((q for q in xsecs if q['type'] == 8 and q['id'] == xid), None)
    tg = next((q for q in xsecs if (q['type'], q['id']) == c['new_target'][:2]), None)
    if xs is None or tg is None: return None
    rx = R.parse(xs['reloc'], 'be')
    e = [(si, so, do) for si, so, do in rx.external if so == c['src']]
    if len(e) != 1 or (xsecs[e[0][0]]['type'], xsecs[e[0][0]]['id'], e[0][2]) != c['xb_target']: return None
    if xs['data'][c['src'] - 4:c['src']] != bytes.fromhex('6a000000'): return None
    po = c['new_target'][2]
    if tg['data'][po + 6:po + 8] != struct.pack('>H', c['proto_vt']) or b'warping lara' not in tg['data']: return None
    r = R.parse(reloc_le, 'le')
    j = k_of(*c['new_target'][:2])
    if j is None: return None
    out = [(j, so, po) if so == c['src'] else (si, so, do) for si, so, do in r.external]
    if out == r.external: return None
    r.external = out
    return R.write(r, 'le')

ANALOG_TRIES = 8
def _analog_build(xd, xw, rx, ax, n, ids, store, have):
    import numpy as np
    t = 7
    xa = store['xb_store'][t, ax]['data']; pc = store['pc_store'][t, ids.base[t][ax]]
    pa = pc['data']; rp = R.parse(pc['reloc'], 'le')
    if rp.external or rx.external: return 'ext_relocs'
    if [a for a, _ in rx.idref] != [a for a, _ in rp.idref] or [a for a, _ in rx.idref_a] != [a for a, _ in rp.idref_a]:
        return 'idref_layout'
    out = bytearray(pa)
    for lx, lp in ((rx.idref, rp.idref), (rx.idref_a, rp.idref_a)):      # id-ref fields: same order on both platforms
        for (ty, ox), (_, op) in zip(lx, lp):
            v, = struct.unpack_from('>I', xd, ox)
            struct.pack_into('<I', out, op, ids(ty, v) if v not in (0, 0xffffffff) else v)
    skx = set(rx.pointer_offsets()) | set(rx.id_offsets()); skp = set(rp.pointer_offsets()) | set(rp.id_offsets())
    aw = np.frombuffer(xa, '>u4', n); pw = np.frombuffer(pa, '<u4', len(pa) // 4)
    diff = [int(i) * 4 for i in np.nonzero(aw != xw)[0] if int(i) * 4 not in skx]
    by_val = collections.defaultdict(list)
    for o in diff: by_val[int(aw[o // 4])].append(o)
    for vb, offs in by_val.items():
        ox = [int(i) * 4 for i in np.nonzero(aw == vb)[0] if int(i) * 4 not in skx]
        vds = [struct.unpack_from('>I', xd, o)[0] for o in offs]
        # clone test: the analog value must be a base section id of type T AND every DLC value a section of type T in THIS DRM
        # (rejects coincidences such as 0 / 0x27 / float words; validated leave-one-out on the base Lara costumes)
        opts = [(ty, m[vb]) for ty, m in sorted(ids.base.items()) if isinstance(ty, int) and ty < 100 and vb in m
                and all(v in have.get(ty, ()) for v in vds)]
        done = False
        for ty, vp in opts:
            op = [int(i) * 4 for i in np.nonzero(pw == vp)[0] if int(i) * 4 not in skp]
            if len(op) != len(ox): continue
            dl = len(pa) - len(xa)              # PC layout = Xbox layout + insertions (or deletions): every zipped pair
            if any(not (min(0, dl) <= b - a <= max(0, dl)) for a, b in zip(ox, op)): continue   # must shift within that
            pos = dict(zip(ox, op))
            for o, vd in zip(offs, vds):
                struct.pack_into('<I', out, pos[o], ids(ty, vd))
            done = True; break
        if not done: return 'unaligned'
    return bytes(out), pc['reloc']

def convert_drm(xsecs, ids, store, media=None, T=None, use_pc_copy=True, use_template=True, use_pc_reauthored=True, use_analog=True,
                analog_exclude=(), extra_fixes=False):
    """Public entry.  extra_fixes (= material 'dlc') also enters the analog id-coincidence guard (tools/analog_idcoin.py, crash 0x5c019f:
    dungeon_main DTP 23793-96 +0x10 matIdx 8 -> 213) so EVERY caller asking for the DLC fixes gets it, not only assemble_dlc.assemble.
    No-op when the guard is already active (assemble's own context); see _convert_drm for the pipeline."""
    import contextlib
    if extra_fixes:
        import analog_idcoin
        ctx = contextlib.nullcontext() if _analog_build is analog_idcoin._build_guarded else analog_idcoin.guarded()
    else:
        ctx = contextlib.nullcontext()
    with ctx:
        return _convert_drm(xsecs, ids, store, media, T, use_pc_copy, use_template, use_pc_reauthored, use_analog, analog_exclude, extra_fixes)

def _convert_drm(xsecs, ids, store, media=None, T=None, use_pc_copy=True, use_template=True, use_pc_reauthored=True, use_analog=True,
                analog_exclude=(), extra_fixes=False):
    """use_pc_reauthored: base scripts that PC re-authored (different layout) and that this DRM carries unchanged are taken
    from PC (route 'pc_reauthored') and the external relocs of every other section into them are translated to the PC layout
    (the engine shares resident sections by id, so a resident PC copy would otherwise be addressed with Xbox offsets)."""
    """xsecs: parsed Xbox sections (drm.sections_with_data dicts). Returns (Drm, report list)."""
    T = T or table()
    ids.local = {}
    new_ids = [ids(s['type'], s['id']) for s in xsecs]
    # the Xbox->PC id map is not a pure function (PC allocates ids per DRM): inside one DRM two sections of a type must not
    # share an id (the engine looks sections up by id). Collisions get a fresh id used for the section AND its references.
    seen = {}; nxt = 3000000
    for k, s in enumerate(xsecs):
        if s['type'] in (0, 13): continue
        key = (s['type'], new_ids[k])
        if key in seen and seen[key] != s['id']:
            lo = ids.local.get((s['type'], s['id']))
            if lo is None:
                lo = nxt; nxt += 1; ids.local[(s['type'], s['id'])] = lo
            new_ids[k] = lo
        else:
            seen[key] = s['id']
    cnt = collections.Counter((s['type'], new_ids[k]) for k, s in enumerate(xsecs))
    index_of = {(s['type'], new_ids[k]): k for k, s in enumerate(xsecs) if cnt[s['type'], new_ids[k]] == 1}
    labs = None; labs0 = None; conv0 = []
    out = []; rep = []; shifts = {}
    for k, s in enumerate(xsecs):
        t, xid, nid = s['type'], s['id'], new_ids[k]
        route = None; data = reloc = None; ver = s['ver']
        if t in MEDIA:
            res = None
            if media is not None:
                try:
                    res = media(t, s, nid, ids)
                except Exception as e:
                    route = 'media_error:%s' % type(e).__name__
            if res is not None:
                data, reloc = res[0], res[1]; route = 'media'
                if len(res) > 2 and res[2] is not None: shifts[k] = res[2]
            else:
                data, reloc = s['data'], R.write(R.parse(s['reloc'], 'be'), 'le'); route = route or 'media_passthrough'
        else:
            bm = ids.base.get(t, {})
            key = (t, xid)
            if use_pc_copy and t in (2, 7, 8, 11) and xid in bm and (t, nid) in store['pc_store'] \
                    and norm_hash(s, xsecs, 'be') in store['xb_hash'].get(key, ()):
                rec = store['pc_store'][t, nid]
                rl = retarget_ext(rec['reloc'], rec['ext'], index_of)
                if rl is not None and len(rec['data']) == s['size']:
                    data, reloc, ver, route = rec['data'], rl, rec['ver'], 'pc_copy'
            if route is None and use_pc_reauthored and t in (7, 8) and key in reauthored(store, ids) \
                    and norm_hash(s, xsecs, 'be') in store['xb_hash'].get(key, ()):
                rec = store['pc_store'][t, reauthored(store, ids)[key]]
                rl = retarget_ext(rec['reloc'], rec['ext'], index_of)
                if rl is not None:
                    data, reloc, ver, route = rec['data'], rl, rec['ver'], 'pc_reauthored'
            if route is None and use_template and t in (7, 8) and xid in bm and key in store['xb_store'] and (t, nid) in store['pc_store']:
                xb = store['xb_store'][key]; pc = store['pc_store'][t, nid]
                if len(xb['data']) == s['size'] == len(pc['data']) and _same_layout(xb['reloc'], s['reloc']):
                    if labs is None: labs = G.drm_labels(xsecs, 'be')
                    rel = R.parse(s['reloc'], 'be')
                    data = template_convert(s['data'], xb['data'], pc['data'], rel, labs[k], T, ids)
                    reloc = R.write(rel, 'le'); route = 'template'; ver = pc['ver']
            if route is None and use_analog and t == 7 and xid not in bm:
                # DLC-new DTP cloned from a base DTP (e.g. dlc_costume_f = lara DTPs + new ids): build from the PC analog.
                # The learned type-7 table mis-converts such structs (u32 counts as u16 pairs, {float,u16,u16} entries) and
                # cannot produce PC re-authored layouts -> crash 0x54e457 (anim-info fill loop, NOTES 2026-10-09 ng_crash).
                res = analog_convert(s, xsecs, ids, store, analog_exclude)
                if res is not None:
                    data, reloc, _ax = res; route = 'analog'
            if route is None:
                rel = R.parse(s['reloc'], 'be')
                if t in (2, 11):
                    data = bytes(CG.CONV[t](s['data'], rel, ids, xid))
                elif t == 8 and _SL() is not None:
                    # Script: typed walker (script_conv) + per-label classes (script_learn); unlabelled words -> old masks
                    if labs is None: labs = G.drm_labels(xsecs, 'be')
                    kmap = {w: (key, ck) for w, key, ck in G.word_keys(len(s['data']), labs[k])}
                    def fb(w, xw, kmap=kmap):
                        c, _ = G.lookup(T, *kmap[w])
                        return c if c is not None else ('raw' if G.is_text(xw) and xw != xw[::-1] else 's32')
                    data, _ = _SL().convert(s['data'], rel, ids, _SL().table(), fallback=fb)
                elif t == 7 and _G0() is not None and _G0().table7() is not None:
                    # DTPData: type-7 table (generic_type0 machinery: extra id classes incl. wave ids, Level-normalised labels)
                    if labs0 is None: labs0 = _G0().labels(xsecs, 'be')
                    data = _G0().convert_section0(s['data'], labs0[k], rel, _G0().table7(), ids, T)
                elif t == 0 and _G0() is not None and _G0().table0() is not None:
                    # type 0: type-0 table with Level-normalised labels; mesh/unit-id overrides applied after the loop
                    if labs0 is None: labs0 = _G0().labels(xsecs, 'be')
                    data = _G0().convert_section0(s['data'], labs0[k], rel, _G0().table0(), ids, T)
                    conv0.append(k)
                else:
                    if labs is None: labs = G.drm_labels(xsecs, 'be')
                    data = G.convert_section(s['data'], t, labs[k], rel, T, ids)
                if t == 13 and len(s['data']) >= 20 and s['data'][:4] == s['data'][12:16] == b'\xbe\xeb\xbe\xeb':
                    # map header (sentinel 0xbeebbeeb): word2 = two BE u16 -> LE u16 pair, word4 = raw bytes (verified on PC
                    # l3_main_bedroom_map and dlc_caverns*_map); the learned table left rare values as s32 (0x10000000 = the 256 MB OOM)
                    xb = s['data']; d13 = bytearray(data)
                    d13[8:12] = struct.pack('<HH', (xb[8] << 8) | xb[9], (xb[10] << 8) | xb[11])
                    d13[16:20] = xb[16:20]
                    data = bytes(d13)
                reloc = R.write(rel, 'le'); route = 'convert'
                if t == 7: conv0.append(k)
        if route in ('convert', 'template') and t in (2, 7, 8, 11) and xid in ids.base.get(t, {}) \
                and norm_hash(s, xsecs, 'be') in store['xb_hash'].get((t, xid), ()):
            import hashlib as _hl                        # base content: section 'ver' as on PC (Script ver = content version
            pv = pc_vers_content().get('%d:%d:%s' % (t, nid, _hl.md5(data).hexdigest()[:16]))   # id): exact PC content first,
            if pv is None and t == 8:                                                           # content modulo dependency order
                import script_conv as _SC
                nk = _hl.md5(_SC.deps_normalized(data, R.parse(reloc, 'le'))).hexdigest()[:16]
                pv = pc_vers_content().get('8:%d:n%s' % (nid, nk))
            if pv is None: pv = pc_vers().get('%d:%d' % (t, nid))                               # else the runtime one
            if pv is not None: ver = pv
        out.append(DW.Section(t, nid, data, reloc, s['flags'], ver, s['spec']))
        rep.append((k, t, xid, nid, route))
    if conv0 and _G0() is not None:   # structural overrides on converted type 0/7 sections (collision mesh arrays,
                                      # unit/portal/terrain-group/intro ids, intro object ids): generic_type0.py
        datas = _G0().apply_overrides(xsecs, [sec.data for sec in out], ids)
        for k in conv0: out[k].data = bytes(datas[k])
    for k, (_, t, _, _, route) in enumerate(rep):      # typed model-DTP fields (HInfo counts: 256 MB OOM, NOTES 2026-10-09)
        if t == 7 and route in ('convert', 'template') and xsecs[k]['data'][:4] == MODEL_MAGIC:
            buf = bytearray(out[k].data)
            if model_fix(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), buf):
                MODEL_STATS['sections_fixed'] += 1
                out[k].data = bytes(buf)
    if extra_fixes:      # model 'point' arrays (TP/HS/HB/HC fields); 38 rules, 0 words changed on the 1055 base pairs (model_point_fix.selftest)
        import model_point_fix                          # agrees with model_fix on HS+16 s32, HB+0/4/8/44 s32, HC+40 s16
        for k, (_, t, _, _, route) in enumerate(rep):
            if t == 7 and route in ('convert', 'template') and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = model_point_fix.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data)
                if lg: out[k].data = nb
    for k, (_, t, _, _, route) in enumerate(rep):      # anim event-list DTPs (crash fix13 0x593659, NOTES 2026-10-10): record
        if t == 7 and route in ('convert', 'template'):  # headers {u16 h, s16 frame} + terminator as u16 pairs, typed fields
            import animfx
            buf = bytearray(out[k].data)
            if animfx.fix(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), buf, ids):
                out[k].data = bytes(buf)
    for k, (_, t, _, _, route) in enumerate(rep):      # 0x390-byte enemy AI records in level DTPs (crash glitchfix_run
        if t == 7 and route in ('convert', 'template'):  # 0x54df84, NOTES 2026-10-10): DTP ids without relocs + s32 fields
            import aidata_fix
            buf = bytearray(out[k].data)
            if aidata_fix.fix(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), buf, ids):
                out[k].data = bytes(buf)
    for k, (_, t, _, _, route) in enumerate(rep):      # SoundPlex DTP words left raw (crash 0x5912a3 type 4; fix18 OOM type 5 COUNT)
        if t == 7 and route in ('convert', 'template'):
            import soundplex_fix, soundplex_nodes
            xd, xr = xsecs[k]['data'], xsecs[k]['reloc']
            if len(out[k].data) != len(xd): continue
            nb, lg = soundplex_fix.fix_section(xd, xr, out[k].data)
            nb, lg2 = soundplex_nodes.fix_section(xd, xr, nb, soundplex_nodes.load_rules())
            if lg or lg2: out[k].data = bytes(nb)
    if extra_fixes:      # DTP id lists (dtplist), DLC-new DTP with a PC-re-authored block (align SPECS: sewer_gate 21105, id unique in the
        import dtp_align_fix as AF, dtpid_sweep as DS   # 300 DLC DRMs), goo fx block; then the dtpid sweep (REAL words only)
        for k, (_, t, xid, _, route) in enumerate(rep):
            if t != 7 or route not in ('convert', 'template') or len(out[k].data) != len(xsecs[k]['data']): continue
            xd, rl = xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be')
            buf = bytearray(out[k].data)
            if AF.is_dtplist(xd, rl): AF.dtplist_fix(xd, rl, buf, ids)
            sp = AF.SPECS.get(('dlc1_uo_sewer_gate.drm', xid))
            if sp and len(xd) == len(store['xb_store'][7, sp['base']]['data']) + 0x60: AF.align_fix(xd, rl, buf, sp, store, ids)
            AF.goo_fix(xd, rl, buf, store, ids)
            out[k].data = bytes(buf)
        class _Shim: pass
        shim = _Shim(); shim.sections = out            # candidates() reads only .sections[k].type/.id/.data
        cs = [c for c in DS.candidates(xsecs, shim, ids, store) if c['st'] != 'ok']   # NB: does NOT reset ids.local (convert_drm's)
        for c in cs: c['cls'] = DS.classify(c, store, ids)
        DS.classify2(cs, {q['id']: (len(q['data']), _reloc_sig(q['reloc'], 'be')) for q in xsecs if q['type'] == 7 and q['data'] is not None})
        for c in cs:
            if c['cls'].startswith('REAL:'):
                b = bytearray(out[c['k']].data); b[c['off']:c['off'] + 4] = struct.pack('<I', c['want']); out[c['k']].data = bytes(b)
    if extra_fixes:      # SoundPlex float/u32 fields left raw (tools/soundplex_fields.py; 0 words changed on 8964 base pairs; s32 + plausibility only)
        import soundplex_fields
        for k, (_, t, _, _, route) in enumerate(rep):
            if t == 7 and route in ('convert', 'template') and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = soundplex_fields.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data, preloc=out[k].reloc)
                if lg: out[k].data = bytes(nb)
    for k, (_, t, _, _, route) in enumerate(rep):      # identifier strings (raw on PC: 14473/14473 base spans) mangled by the
        if t in (0, 7, 8) and route in ('convert', 'template'):   # learned tables ('chain_free' -> 'hcian_free', NOTES
            import dtp_audit                                    # 2026-10-12) + SoundPlex root node type word0 (s32, 1914/1914)
            nb, lg = dtp_audit.fix_strings(xsecs[k]['data'], xsecs[k]['reloc'], out[k].data, t, preloc=out[k].reloc)
            if lg: out[k].data = bytes(nb)
    for k, (_, t, _, _, route) in enumerate(rep):      # Script classes deriving from PC-grown base classes (crash ng3)
        if t == 8 and route == 'convert' and len(xsecs[k]['data']) >= 0x54:
            sh = script_layout_shift(struct.unpack_from('>I', xsecs[k]['data'], 0x18)[0], xsecs, store, ids)
            if sh is None: REBASE_STATS['unresolved_chain'] += 1; continue
            if not sh: continue
            buf = bytearray(out[k].data)
            REBASE_STATS['words'] += script_rebase(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), buf, sh)
            REBASE_STATS['scripts'] += 1
            out[k].data = bytes(buf)
    if extra_fixes:      # script SArray counts (u32 @ptr-4): raw / u16-pair copies of the Xbox count -> Xbox count LE (crash class 'protos 6 -> 0x60000').
        import script_conv as SC                       # Same rule as engine_walk_check.fix_sarray; guard = identical internal-reloc offsets.
        for k, (_, t, _, _, route) in enumerate(rep):  # Idempotent (writes only when the word is not already LE). 0 words on 52615 base sections.
            if t != 8 or route not in ('convert', 'template') or len(out[k].data) != len(xsecs[k]['data']): continue
            xd, xr = xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be')
            if sorted(xr.internal) != sorted(R.parse(out[k].reloc, 'le').internal): continue
            try: arrays = SC.Walk(xd, xr, 'be').run().arrays
            except Exception: continue
            buf = bytearray(out[k].data)
            for nm, at, cnt, sz in arrays:
                if nm == 'vtable' or at < 4: continue
                xb = xd[at - 4:at]
                if bytes(buf[at - 4:at]) in (xb, xb[1::-1] + xb[:1:-1]) and xb[::-1] != bytes(buf[at - 4:at]):
                    buf[at - 4:at] = xb[::-1]
            out[k].data = bytes(buf)
    for k, (_, t, xid, _, route) in enumerate(rep):
        if t == 8 and route == 'convert' and xid in CINE_NOWAIT:
            buf = bytearray(out[k].data)
            if cine_nowait(xid, xsecs[k]['data'], buf): out[k].data = bytes(buf)
    if extra_fixes:      # tag-0x403 object-id record {0x403,0,0,0x30000}: +0x30 id left RAW (0x000000dd -> 0xdd000000) by the learned table -> bitset index
        import tag403_fix                              # out of range, AV 0x5d60bb (crash5d: dungeonhalla 20493, hallb 20133, caverns 20872). s32 + range
        for k, (_, t, _, _, route) in enumerate(rep):  # guard 1..0x101f; 0 words on 8964 base pairs; idempotent. Runs after apply_overrides / fix_strings.
            if t == 7 and route in ('convert', 'template') and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = tag403_fix.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data)
                if lg: out[k].data = bytes(nb)
    if extra_fixes:      # cell portal words {u16 start, u16 count} left u32 (04 00 50 00 instead of 50 00 04 00): overlapping vertex ranges -> stack overflow in
        import portal_fix                              # the frustum clip fn 0x567d90, AV 0x167f01 (crash167: dlc_dungeon type-0 sec 47 x8, 51 x1). Heuristic rule
        for k, (_, t, _, _, route) in enumerate(rep):  # (marker 0xbeebbeeb at +-0x40, halves in 1..0x3ff), 0 words on 1975 base type-0 sections; idempotent.
            if t == 0 and route == 'convert' and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = portal_fix.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data)
                if lg: out[k].data = bytes(nb)
    if extra_fixes:      # uberobject graph descriptor DESC: model_idx word (+0x18: dragon_slider 20457 00020000 -> 02000000, 'failed to create rigid body') and
        import dtp_descfix                             # flag word (+0x50: raft_bridge 20765 ffff0001 -> ffff0100, chain Shot node never fired). dtp_schema.convert
        for k, (_, t, _, _, route) in enumerate(rep):  # restricted to those two DESC words (dtp_descfix.ALLOWED_WORDS); TRANS / tag C NOT written. 0 on 8964 base pairs.
            if t == 7 and route in ('convert', 'template') and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = dtp_descfix.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data, R.parse(out[k].reloc, 'le'))
                if lg: out[k].data = bytes(nb)
    if extra_fixes:      # uberobject link joint {0x0b, ptr A, ptr B, f32 ratio}: +0xc left RAW (byte0-first like joint selectors) but read as float by
        import link_ratio_fix                          # FUN_004d7ed0 (0x4d7f31 fld): sewer_gate 20754 -2.0 -> ~0, bar decoupled, gate never opens (B84).
        for k, (_, t, _, _, route) in enumerate(rep):  # base 23/23 links s32, 0 words changed on 8964 base pairs; idempotent.
            if t == 7 and route in ('convert', 'template') and len(out[k].data) == len(xsecs[k]['data']):
                nb, lg = link_ratio_fix.fix_section(xsecs[k]['data'], R.parse(xsecs[k]['reloc'], 'be'), out[k].data)
                if lg: out[k].data = bytes(nb)
    pcl = {k for k, (_, t, xid, _, route) in enumerate(rep) if route == 'pc_reauthored' or (route == 'pc_copy' and (t, xid) in reauthored(store, ids))}
    if pcl:         # external pointers of our converted sections INTO PC-layout re-authored scripts: translate offsets
        for k, sec in enumerate(out):
            if not sec.reloc or rep[k][4] not in ('convert', 'template'): continue
            r = R.parse(sec.reloc, 'le')
            if not any(si in pcl for si, _, _ in r.external): continue
            ext = []
            for si, so, do in r.external:
                if si in pcl:
                    m = xlate_map(store, ids, (xsecs[si]['type'], xsecs[si]['id']))
                    if do in m: do = m[do]
                    else: XLATE_STATS['unmapped'] += 1
                    XLATE_STATS['n'] += 1
                ext.append((si, so, do))
            r.external = ext; sec.reloc = R.write(r, 'le')
    for k, (_, t, xid, _, route) in enumerate(rep):    # skip the DLC1 intro cinematic (CINE_SKIP)
        if t == 8 and route == 'convert' and xid in CINE_SKIP:
            rl = cine_skip_reloc(xid, xsecs, out[k].reloc,
                                 lambda tt, xx: next((j for j, q in enumerate(xsecs) if (q['type'], q['id']) == (tt, xx)), None))
            if rl is not None: out[k].reloc = rl
    if shifts:      # media converters that moved data (mesh rebatch): fix external pointers INTO them
        for sec in out:
            if not sec.reloc: continue
            r = R.parse(sec.reloc, 'le')
            if any(si in shifts for si, _, _ in r.external):
                r.external = [(si, so, shifts[si](do) if si in shifts else do) for si, so, do in r.external]
                sec.reloc = R.write(r, 'le')
    return out, rep

def default_media(t, s, nid, ids, wave='silence'):
    """Media converters of the other agents (textures/audio/render), wired to the shared DlcIds.
    Returns (data, reloc_le[, shift_fn]). Shader libraries (9) have no converter here (Xenos microcode;
    see work/render) -> raise -> passthrough flagged in the report."""
    xd, xr = s['data'], s['reloc']
    if t == 5:
        import tex_convert
        return tex_convert.convert(xd), b''
    if t == 6:
        import wave_convert
        f = wave_convert.silence_for_xbox_wave if wave == 'silence' else wave_convert.xbox_wave_to_pc
        return f(xd), b''
    if t == 12:
        import terrain_convert, mesh_convert
        if terrain_convert.is_terrain(xd):
            return terrain_convert.convert(xd, xr, ids)
        info = {}
        d, r = mesh_convert.convert(xd, xr, ids, info)
        sh = info.get('shift')
        return d, r, (sh if callable(sh) else (lambda o, m=sh: m.get(o, o)) if sh else None)
    if t == 10:
        import material_convert
        return material_convert.convert(xd, xr, shader_map=lambda x: ids(9, x), tex_map=lambda x: ids(5, x))
    raise NotImplementedError('no converter for section type %d' % t)

def _same_layout(a_be, b_be):
    ra, rb = R.parse(a_be, 'be'), R.parse(b_be, 'be')
    return ra.internal == rb.internal and ra.idref == rb.idref and ra.idref_a == rb.idref_a and \
        [(so, do) for _, so, do in ra.external] == [(so, do) for _, so, do in rb.external]

def convert_file(raw_xbox, ids, store, media=default_media, endian_out='le', cdrm=True):
    """Xbox DRM/CDRM bytes -> (PC DRM bytes (CDRM if cdrm), report)."""
    from drm import cdrm_decode, sections_with_data
    X = DW.read(raw_xbox, 'be')
    h, xsecs = sections_with_data(cdrm_decode(raw_xbox, 'be'), 'be')
    secs, rep = convert_drm(xsecs, ids, store, media)
    D = DW.Drm(secs, X.names, X.pad, X.ver, X.u0, X.u1)
    raw = D.write(endian_out)
    return (DW.cdrm_encode(raw, endian_out) if cdrm else raw), rep

if __name__ == '__main__':
    import generic_store
    store = generic_store.load()
    dlc = pickle.load(open(os.path.join(W, 'dlc_drms.pkl'), 'rb'))
    ids = DlcIds(store, dlc, rebuild=True)
    print('new ids per type', {t: len(v) for t, v in ids.new.items()},
          'reassigned (collisions)', {t: sum(1 for a, b in v.items() if a != b) for t, v in ids.new.items()})
    print('symbols', ids.sym_info)
