"""Learn / apply / evaluate the Xbox->PC word permutation per semantic label of the typed Script walker
(script_conv.Walk).  Table = {label: Counter(class -> #words where the class reproduces the PC word)}; lookup
falls back from the full label to shorter prefixes, then to the walker's prior kind.

Usage: tools/venv/bin/python -I tools/script_learn.py [eval|save]
  eval : 2-fold held-out (split by Script name symbol, so all copies/versions of one script are in one fold)
         + in-sample, per-pair exactness and residual categories
  save : train on all pairs -> work/script/script_table.pkl
"""
import sys, os, struct, collections, pickle, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
import script_conv as S
WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'script')
TABLE = os.path.join(WS, 'script_table.pkl')

CLASSES = ('s32', 's16', 'raw', 'b2s16', 's16b2', 'id16a:100', 'id16b:100', 'id16ab:100', 'id32:8', 'syma_r', 'r_symb',
           # other id spaces referenced from script data (native init blocks, code operands): DTP ids, object ids (u16),
           # unit ids (u16), intro unique ids (u32, generic_type0 113), localisation string ids (101, tools/locals.py)
           'id32:7', 'id16a:11', 'id16a:110', 'id32:113', 'id16a:101', 'id32:101', 'id32:6', 'id32:114')
PREF = {c: i for i, c in enumerate(CLASSES)}

def apply_word(xw, c, ids):
    if c == 'syma_r':
        a, = struct.unpack('>H', xw[:2])
        return struct.pack('<H', ids(G.SYM, a) & 0xffff if a not in (0, 0xffff) else a) + xw[2:4]
    if c == 'r_symb':
        b, = struct.unpack('>H', xw[2:4])
        return xw[0:2] + struct.pack('<H', ids(G.SYM, b) & 0xffff if b not in (0, 0xffff) else b)
    if c.startswith('id16'):
        which, t = c[4:].split(':'); t = int(t)
        a, b = struct.unpack('>HH', xw)
        if 'a' in which and a not in (0, 0xffff): a = ids(t, a) & 0xffff
        if 'b' in which and b not in (0, 0xffff): b = ids(t, b) & 0xffff
        return struct.pack('<HH', a, b)
    return G.apply_word(xw, c, ids)

def _shape(xw):
    import generic_type0
    return generic_type0.shape(xw)

def prefixes(lab):
    for k in range(len(lab), 0, -1):
        yield lab[:k]

class Table:
    def __init__(self, v=None, prior=None):
        self.v = v if v is not None else collections.defaultdict(collections.Counter)
        self.prior = prior if prior is not None else {}
        self._best = {}
    def add(self, lab, cs):
        for p in prefixes(lab):
            c = self.v[p]
            for x in cs: c[x] += 1
            c['#'] += 1
    def best(self, lab):
        r = self._best.get(lab)
        if r is None:
            r = self._best[lab] = self._compute(lab)
        return r
    def _compute(self, lab):
        for p in prefixes(lab):
            c = self.v.get(p)
            if c and len(c) > 1:
                pri = self.prior.get(lab) or self.prior.get(p)
                return max((k for k in c if k != '#'), key=lambda k: (c[k], k == pri, -PREF.get(k, 99)))
        return self.prior.get(lab, 's32')
    def dump(self):
        return dict(v={k: dict(c) for k, c in self.v.items()}, prior=dict(self.prior))
    @classmethod
    def load(cls, path=TABLE):
        d = pickle.load(open(path, 'rb'))
        return cls(collections.defaultdict(collections.Counter, {k: collections.Counter(c) for k, c in d['v'].items()}), d['prior'])

def train(pairs, ids, T=None):
    T = T or Table()
    for r in pairs:
        rel = R.parse(r['xr'], 'be')
        W = S.walk(r['xd'], rel)
        for k, v in W.prior.items(): T.prior.setdefault(k, v)
        skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
        xd, pd = r['xd'], r['pd']
        for w, lab in W.lab.items():
            if w in skip: continue
            xw, pw = xd[w:w + 4], pd[w:w + 4]
            outs = {c: apply_word(xw, c, ids) for c in CLASSES}
            if len(set(outs.values())) == 1: continue           # no information
            cs = [c for c, o in outs.items() if o == pw]
            T.add(lab + ('~' + _shape(xw),), cs)        # most specific level: value shape (prefixes = plain label)
    return T

def convert(xd, rel, ids, T, fallback=None, W=None):
    """xd: Xbox section data, rel: parsed BE reloc. fallback(w, xw) -> class for words the walker did not label."""
    W = W or S.walk(xd, rel)
    out = bytearray(xd)
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    for w in range(0, len(xd) // 4 * 4, 4):
        if w in skip: continue
        xw = xd[w:w + 4]
        lab = W.lab.get(w)
        if lab is not None: c = T.best(lab + ('~' + _shape(xw),))
        elif fallback is not None: c = fallback(w, xw)
        else: c = 'raw' if G.is_text(xw) and xw != xw[::-1] else 's32'
        out[w:w + 4] = apply_word(xw, c, ids)
    for o in rel.pointer_offsets():
        out[o:o + 4] = xd[o:o + 4][::-1]
    for o, t in rel.id_offsets().items():
        v, = struct.unpack_from('>I', xd, o)
        struct.pack_into('<I', out, o, ids(t, v) if v not in (0, 0xffffffff) else v)
    return bytes(out), W

_TAB = None
def table():
    global _TAB
    if _TAB is None: _TAB = Table.load(TABLE)
    return _TAB

# ------------------------------------------------------------------------------- evaluation
def name_key(r):
    return struct.unpack_from('>H', r['xd'], 8)[0] if len(r['xd']) >= 12 else 0

def folds(pairs):
    A = [r for r in pairs if zlib.crc32(b'%d' % name_key(r)) & 1 == 0]
    B = [r for r in pairs if zlib.crc32(b'%d' % name_key(r)) & 1 == 1]
    return A, B

def evaluate(pairs, ids, T, st=None, detail=None):
    st = st if st is not None else collections.Counter()
    for r in pairs:
        rel = R.parse(r['xr'], 'be')
        d, W = convert(r['xd'], rel, ids, T)
        st['n'] += 1
        pd = r['pd']
        if d == pd: st['exact'] += 1; continue
        bad = [w for w in range(0, len(d), 4) if d[w:w + 4] != pd[w:w + 4]]
        st['badwords'] += len(bad)
        # (a) dependency array order: PC order is build-order dependent (not derivable), runtime-irrelevant
        deps = [(t, n) for nm_, t, n, sz in W.arrays if nm_ == 'deps']
        dset = {t + 4 * k for t, n in deps for k in range(n)}
        nd = [w for w in bad if w not in dset]
        if not nd and all(sorted(d[t + 4 * k:t + 4 * k + 4] for k in range(n)) == sorted(pd[t + 4 * k:t + 4 * k + 4] for k in range(n)) for t, n in deps):
            st['exact_mod_deps'] += 1
        else:
            # (b) PC content differs: some wrong word that NO class reproduces (re-authored script / map gap)
            unexpl = sum(1 for w in nd if w + 4 <= len(d) and all(apply_word(r['xd'][w:w + 4], c, ids) != pd[w:w + 4] for c in CLASSES))
            st['pc_differs' if unexpl else 'explainable_wrong'] += 1
        labs = collections.Counter(W.lab.get(w, ('unk',))[:2] for w in bad)
        for l, n in labs.items(): st['lab', l] += n
        if detail is not None: detail.append((r['name'], r['xid'], len(bad), labs.most_common(3)))
    return st

def report(st, title):
    n = st['n']
    print('-- %s: %d pairs, exact %d = %.2f%%, exact-mod-dependency-order %d = %.2f%%, wrong words %d' % (title, n, st['exact'],
          100. * st['exact'] / max(1, n), st['exact'] + st['exact_mod_deps'], 100. * (st['exact'] + st['exact_mod_deps']) / max(1, n), st['badwords']))
    conv = n - st['pc_differs']
    print('   PC content differs (a wrong word no class reproduces): %d ; over the convertible rest (%d): exact-mod-deps %.2f%%, '
          'explainable wrong %d' % (st['pc_differs'], conv, 100. * (st['exact'] + st['exact_mod_deps']) / max(1, conv), st['explainable_wrong']))
    for k, v in sorted(((k, v) for k, v in st.items() if isinstance(k, tuple)), key=lambda kv: -kv[1])[:25]:
        print('     %-50s %d' % (k[1], v))

def load_pairs(t=8):
    return pickle.load(open(os.path.join(WS, 'pairs_%d.pkl' % t), 'rb'))

if __name__ == '__main__' and sys.argv[1:2] != ['symmap']:
    import dlc_generic as DG
    ids = DG.DlcIds()
    P = load_pairs(8)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'eval'
    if mode == 'eval':
        A, B = folds(P)
        TA = train(A, ids); TB = train(B, ids)
        st = evaluate(B, ids, TA); evaluate(A, ids, TB, st)
        report(st, 'HELD-OUT (2-fold by script name)')
    T = train(P, ids)
    det = []
    report(evaluate(P, ids, T, detail=det), 'IN-SAMPLE')
    pickle.dump(det, open(os.path.join(WS, 'detail.pkl'), 'wb'))
    if mode in ('save', 'eval'):
        pickle.dump(T.dump(), open(TABLE, 'wb'))

# ------------------------------------------------------------------------------- symbol map
SYM_FIELDS_AB = (('proto', 8), ('state',), ('root', 8))

def symbol_votes(pairs):
    """(xsym -> pcsym) votes from walker fields that are certainly Symbols (prototype/state/script names,
    DataMember names with an equal u16 offset, DataType userType with an equal pad half)."""
    v = collections.defaultdict(collections.Counter)
    for r in pairs:
        rel = R.parse(r['xr'], 'be'); W = S.walk(r['xd'], rel)
        xd, pd = r['xd'], r['pd']
        for w, lab in W.lab.items():
            xa, xb = struct.unpack_from('>HH', xd, w); pa, pb = struct.unpack_from('<HH', pd, w)
            h = lab[0]
            if lab in SYM_FIELDS_AB:
                v[xa][pa] += 1; v[xb][pb] += 1
            elif h == 'dm.off' or lab == ('root', 0x4c):
                if xa == pa: v[xb][pb] += 1
            elif h == 'dt.user':
                if xb == pb or xb == ((pb & 0xff) << 8 | pb >> 8): v[xa][pa] += 1
    v.pop(0, None); v.pop(0xffff, None)
    return v

def build_symmap(pairs, old):
    """script-field votes are authoritative (they disagree with the old raw-vote bootstrap map on 125 low
    symbols, e.g. 26->26 not 26->48); old entries are kept for symbols the scripts never vote on, unless they
    would collide with a script-voted PC symbol."""
    v = symbol_votes(pairs)
    m = {}
    for x, c in v.items():
        (p, n), = c.most_common(1)
        if n >= 0.8 * sum(c.values()): m[x] = p
    inv = collections.Counter(m.values())
    m = {x: p for x, p in m.items() if inv[p] == 1}
    used = set(m.values()); kept = 0
    for x, p in old.items():
        if x not in m and p not in used: m[x] = p; used.add(p); kept += 1
    return m, dict(script_voted=len(m) - kept, kept_old=kept, old=len(old))

if __name__ == '__main__' and sys.argv[1:2] == ['symmap']:
    import json, shutil
    from generic_ids import section_matches
    path = os.path.join(G.W, 'idmap.json')
    bak = os.path.join(G.W, 'idmap_pre_script.json')
    if not os.path.exists(bak): shutil.copy(path, bak)
    d = json.load(open(path))                    # CURRENT map (other tools add entries too); only key 100 is touched
    old = {int(a): b for a, b in d['100'].items()}
    m, info = build_symmap(load_pairs(8), old)
    d['100'] = {str(a): b for a, b in sorted(m.items())}
    json.dump(d, open(path, 'w'))
    print('symbol map', info, 'total', len(m))
