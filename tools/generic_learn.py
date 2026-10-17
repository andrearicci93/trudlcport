"""Learned field-width masks for generic DRM sections (types 0, 7, 8, 13; usable for any type).

Idea: every section is split into REGIONS at offset 0, every internal reloc target and every external
reloc destination.  Each region gets a structural LABEL from the pointer graph:
    root region of a section     -> (type, 'R', referrer-label)      referrer = idref that names it
                                     or (type, 'R', 'size', size) when nothing in the DRM references it
    region reached by a pointer  -> (parent-label, field-offset-in-parent)
Every 4-aligned word of a section is keyed by (label of the region containing it, offset in region).
From the Xbox<->PC pairs we vote, per key, which CLASS turns the Xbox word into the PC word:
    s32 | s16 (2 x u16) | raw (bytes) | b2s16 (2 bytes + u16) | s16b2 (u16 + 2 bytes)
    id32:T (u32 section id of type T, remapped) | id16a:T / id16b:T (u16 id in first / second half)
Palindromic words (00000000, ffffffff, ...) give no evidence.  Unknown keys fall back to a
per-type default chain: (label) -> (type,'R','size',*) generic -> heuristic (ASCII runs stay raw,
otherwise s32).
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')

BASIC = ('s32', 's16', 'raw', 'b2s16', 's16b2')
PERM = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
ID_TYPES = (2, 5, 6, 7, 8, 9, 10, 11, 12)       # section types whose ids appear in data (6 = wave ids in sound DTPs, no reloc)
PREF = {c: i for i, c in enumerate(BASIC)}

def perm(w, c):
    p = PERM[c]
    return bytes((w[p[0]], w[p[1]], w[p[2]], w[p[3]]))

# ------------------------------------------------------------------------------- labels
DEPTH = 6          # number of trailing path components kept in a label (full key)
MID = 3            # components kept in the intermediate fallback key

SCRIPT_WALKER = True        # convert_section(type 8) -> script_learn (set False for the old per-word masks)
ROOT_EXACT_DTP = False      # generic_type0 sets True (type-0/7 tables were trained with it)

def _root(s):
    t = s['type']
    if t == 8: return ('S',)                         # every Script section root is a ScriptTypeStreamData
    if t == 11: return ('O',)
    if t == 7 and ROOT_EXACT_DTP: return ('T', t, s['size'])   # same-size DTP roots are (nearly always) the same template
    return ('T', t, s['size'] if s['size'] < 2048 else 'big')

def _child(pl, f, t=None):
    """label of a region reached from region-label pl through a field at normalized offset f."""
    path = pl[1] + ((('x', t, f) if t is not None else f),)
    return (pl[0], path[-DEPTH:])

def drm_labels(secs, endian='be', types=None, roots=None):
    """secs: parsed DRM sections (with 'reloc' and 'data'); returns {sec_index: [(start, label, stride)]}.
    label = (root, path) ; stride = array element size of the region (0 = not an array).
    roots: optional {sec_index: root label} overriding _root() (e.g. ('LVL',) for a unit's Level section)."""
    import bisect
    _r = (lambda s: roots[s['i']] if s['i'] in roots else _root(s)) if roots else _root
    e = '>' if endian == 'be' else '<'
    rel = {s['i']: R.parse(s['reloc'], endian) for s in secs}
    byid = {(s['type'], s['id']): s['i'] for s in secs}
    starts = collections.defaultdict(set)
    edges = collections.defaultdict(list)          # sec -> [(src_off, dst_sec, dst_off, is_idref)]
    for s in secs:
        i = s['i']; starts[i].add(0)
        r = rel[i]
        for o, t in r.internal:
            if t < s['size']: starts[i].add(t)
            edges[i].append((o, i, t, False))
        for si, o, d in r.external:
            if si < len(secs):
                if d < secs[si]['size']: starts[si].add(d)
                edges[i].append((o, si, d, False))
        for t, o in r.idref + r.idref_a:
            if s['data'] is None or o + 4 > len(s['data']): continue
            v, = struct.unpack_from(e + 'I', s['data'], o)
            j = byid.get((t, v))
            if j is not None and j != i: edges[i].append((o, j, 0, True))
    st = {i: sorted(v) for i, v in starts.items()}
    stride = {}
    for i, l in st.items():
        d = secs[i]['data']; n = secs[i]['size']
        for k, o in enumerate(l):
            L = (l[k + 1] if k + 1 < len(l) else n) - o
            S = 0
            if d is not None and o >= 4 and L > 0:
                c, = struct.unpack_from(e + 'I', d, o - 4)
                if 2 <= c <= 100000:
                    for LL in (L, L - 4, L - 2, L - 1, L - 3):
                        if LL > 0 and LL % c == 0 and (LL // c) % 4 == 0 and LL // c <= 4096:
                            S = LL // c; break
            stride[i, o] = S
    def region_of(i, o):
        k = bisect.bisect_right(st[i], o) - 1
        return st[i][max(k, 0)]
    label = {}
    q = collections.deque()
    referenced = {j for i, es in edges.items() for o, j, d, idr in es if j != i and d == 0}
    for s in secs:
        if s['i'] not in referenced or s['type'] in (8, 11) or (roots and s['i'] in roots):
            label[(s['i'], 0)] = (_r(s), ())
            q.append(s['i'])
    done = set()
    def visit(i):
        for o, j, d, idr in sorted(edges.get(i, ())):
            ps = region_of(i, o)
            pl = label.get((i, ps))
            if pl is None: continue
            key = (j, region_of(j, d) if d < secs[j]['size'] else d)
            if key in label or key[1] != d: continue
            S = stride.get((i, ps), 0)
            f = o - ps
            if S and f < S * 100000: f = f % S
            label[key] = _child(pl, f, secs[j]['type'] if j != i else None)
            if j != i:
                done.discard(j); q.append(j)      # (re)flood j: it may have been flooded before this label existed
    def flood(i):
        for _ in range(256):
            before = len(label); visit(i)
            if len(label) == before: break
    def drain():
        while q:
            i = q.popleft()
            if i in done: continue
            flood(i); done.add(i)
    drain()
    for s in secs:
        if (s['i'], 0) not in label:
            label[(s['i'], 0)] = (_r(s), ()); done.discard(s['i']); q.append(s['i']); drain()
    out = {}
    for i in st:
        if types is not None and secs[i]['type'] not in types: continue
        out[i] = [(o, label.get((i, o), (('orphan', secs[i]['type']), ())), stride.get((i, o), 0)) for o in st[i]]
    return out

def mid(key):
    lab, f = key
    return ('M', (lab[0], lab[1][-MID:]), f)

def lookup(T, key, ck):
    """class for a word: full label key -> shorter-path key -> coarse key; (None, 'fallback') if unknown"""
    for k, src in ((key, 'label'), (mid(key), 'mid'), (('C',) + ck, 'coarse'), (('R', key[0]), 'region')):
        c = T.best(k)
        if c is not None and c != '?': return c, src
    return None, 'fallback'

def word_keys(size, regions):
    """yield (word_offset, key, coarse_key) for every aligned word.
    key = (label, offset-in-region mod stride); coarse = (root, last path component, offset)"""
    k = 0; n = len(regions)
    for w in range(0, size // 4 * 4, 4):
        while k + 1 < n and regions[k + 1][0] <= w: k += 1
        o, lab, S = regions[k]
        f = w - o
        if S: f = f % S
        yield w, (lab, f), (lab[0], lab[1][-1:], f)

# ------------------------------------------------------------------------------- training
SYM = 100                                        # pseudo section type: script Symbol ids (u16)
ID16_TYPES = (2, 7, 8, 11, SYM)

def word_classes(xw, pw, idm):
    """list of classes consistent with X word -> PC word (None if palindromic/no evidence)."""
    if xw == xw[::-1] and xw == pw: return None
    cs = [c for c in BASIC if perm(xw, c) == pw]
    v, = struct.unpack('>I', xw); pv, = struct.unpack('<I', pw)
    for t in ID_TYPES:
        m = idm.get(t)
        if m and v in m and m[v] == pv and m[v] != v: cs.append('id32:%d' % t)
    a, b = struct.unpack('>HH', xw); pa, pb = struct.unpack('<HH', pw)
    for t in ID16_TYPES:
        m = idm.get(t)
        if not m: continue
        ma = a in m and m[a] == pa and m[a] != a
        mb = b in m and m[b] == pb and m[b] != b
        if ma and (b == pb): cs.append('id16a:%d' % t)
        if mb and (a == pa): cs.append('id16b:%d' % t)
        if ma and mb: cs.append('id16ab:%d' % t)
    if 's16' in cs and SYM in idm:
        # a Symbol field holding an identity-mapped (or null) symbol is indistinguishable from s16: count it
        # as compatible with the symbol classes too, so mostly-low-symbol fields still learn id16*:SYM
        m = idm[SYM]
        ia = a in (0, 0xffff) or m.get(a) == a
        ib = b in (0, 0xffff) or m.get(b) == b
        if ia: cs.append('id16a:%d' % SYM)
        if ib: cs.append('id16b:%d' % SYM)
        if ia and ib: cs.append('id16ab:%d' % SYM)
    return cs

class Table:
    def __init__(self):
        self.v = collections.defaultdict(collections.Counter)   # key -> Counter(class)
        self.n = collections.Counter()                            # key -> #instances with evidence
    def add(self, key, cs):
        self.n[key] += 1
        for c in cs: self.v[key][c] += 1
    def best(self, key):
        c = self.v.get(key)
        if not c: return None
        items = [kv for kv in c.items() if kv[0] != '?'] or list(c.items())   # '?' = no class explains it
        return max(items, key=lambda kv: (kv[1], -PREF.get(kv[0], 9)))[0]

def train(P, names, idm, types=(0, 7, 8, 13), matches=None):
    from generic_ids import section_matches
    T = Table()
    for nm in names:
        x, p = P[nm]
        sx, sp = x[1], p[1]
        mt = section_matches(sx, sp, idm)
        labs = drm_labels(sx, 'be', types)
        for i, j, _ in mt:
            a, b = sx[i], sp[j]
            if a['type'] not in types or a['size'] != b['size'] or a['data'] is None: continue
            rel = R.parse(a['reloc'], 'be')
            skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            da, db = a['data'], b['data']
            for w, key, ck in word_keys(a['size'], labs[i]):
                if w in skip: continue
                cs = word_classes(da[w:w + 4], db[w:w + 4], idm)
                if cs is None: continue
                T.add(key, cs if cs else ['?'])
                T.add(mid(key), cs if cs else ['?'])
                T.add(('R', key[0]), cs if cs else ['?'])
                T.add(('C',) + ck, cs if cs else ['?'])
    return T

# ------------------------------------------------------------------------------- applying
def is_text(w):
    return all(32 <= c < 127 or c == 0 for c in w) and any(32 < c < 127 for c in w)

def apply_word(xw, c, ids):
    if c in PERM: return perm(xw, c)
    if c.startswith('id32:'):
        v, = struct.unpack('>I', xw)
        return struct.pack('<I', ids(int(c[5:]), v) if v not in (0, 0xffffffff) else v)
    if c.startswith('id16'):
        which, t = c[4:].split(':'); t = int(t)
        a, b = struct.unpack('>HH', xw)
        if 'a' in which and a != 0xffff: a = ids(t, a) & 0xffff
        if 'b' in which and b != 0xffff: b = ids(t, b) & 0xffff
        return struct.pack('<HH', a, b)
    return perm(xw, 's32')

def convert_section(x, sec_type, regions, rel, T, ids, stats=None):
    if sec_type == 8 and SCRIPT_WALKER:      # Script: typed walker + learned per-label classes (script_learn.py)
        try:
            import script_learn as SL
            kmap = {w: (key, ck) for w, key, ck in word_keys(len(x), regions)}
            def fb(w, xw):
                c, _ = lookup(T, *kmap[w])
                return c if c is not None else ('raw' if is_text(xw) and xw != xw[::-1] else 's32')
            return SL.convert(x, rel, ids, SL.table(), fallback=fb)[0]
        except FileNotFoundError:
            pass
    out = bytearray(x)
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    for w, key, ck in word_keys(len(x), regions):
        if w in skip: continue
        xw = x[w:w + 4]
        c, src = lookup(T, key, ck)
        if c is None:
            src = 'fallback'
            c = 'raw' if is_text(xw) and xw != xw[::-1] else 's32'
        if stats is not None: stats[src] += 1
        out[w:w + 4] = apply_word(xw, c, ids)
    for o in rel.pointer_offsets():
        out[o:o + 4] = x[o:o + 4][::-1]
    for o, t in rel.id_offsets().items():
        v, = struct.unpack_from('>I', x, o)
        struct.pack_into('<I', out, o, ids(t, v) if v not in (0, 0xffffffff) else v)
    return bytes(out)

# ------------------------------------------------------------------------------- evaluation
def evaluate(P, names, T, idm, types=(0, 7, 8, 13), detail=None):
    from generic_ids import section_matches
    from convert_generic import IdMapper
    ids = IdMapper()
    st = collections.Counter()
    for nm in names:
        x, p = P[nm]; sx, sp = x[1], p[1]
        mt = section_matches(sx, sp, idm)
        labs = drm_labels(sx, 'be', types)
        for i, j, _ in mt:
            a, b = sx[i], sp[j]
            t = a['type']
            if t not in types or a['data'] is None: continue
            if a['size'] != b['size']: st[t, 'size_differs'] += 1; continue
            d = convert_section(a['data'], t, labs[i], R.parse(a['reloc'], 'be'), T, ids, st)
            st[t, 'n'] += 1; st[t, 'bytes'] += len(d)
            if d == b['data']: st[t, 'exact'] += 1
            else:
                bw = sum(1 for k in range(0, len(d), 4) if d[k:k + 4] != b['data'][k:k + 4])
                st[t, 'badwords'] += bw
                if detail is not None and len(detail[t]) < 3000: detail[t].append((nm, i, j, bw))
    return st

def report(st, title):
    print('--', title, ' (labelled words %d, mid %d, coarse %d, region-majority %d, fallback words %d)' % (st['label'], st['mid'], st['coarse'], st['region'], st['fallback']))
    for t in sorted({k[0] for k in st if isinstance(k, tuple)}):
        n = st[t, 'n']
        if not n: continue
        print('  type %2d: %6d equal-size pairs, exact %6d = %6.2f%%   wrong words %.3f%%   (size differs: %d)' % (
            t, n, st[t, 'exact'], 100. * st[t, 'exact'] / n, 100. * st[t, 'badwords'] * 4 / max(1, st[t, 'bytes']), st[t, 'size_differs']))

if __name__ == '__main__':
    import json, zlib
    from convert_generic import IdMapper
    from generic_cache import load_pairs
    P = load_pairs()
    idm = IdMapper().m
    names = sorted(P)
    A = [n for n in names if zlib.crc32(n.encode()) & 1 == 0]
    B = [n for n in names if zlib.crc32(n.encode()) & 1 == 1]
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if mode in ('holdout', 'all'):
        TA = train(P, A, idm); TB = train(P, B, idm)
        sa = evaluate(P, B, TA, idm); sb = evaluate(P, A, TB, idm)
        report(sa + sb, 'HELD-OUT (2-fold by DRM name)')
    if mode in ('insample', 'all', 'save'):
        T = train(P, names, idm)
        det = collections.defaultdict(list)
        s = evaluate(P, names, T, idm, detail=det)
        report(s, 'IN-SAMPLE (trained on all pairs)')
        pickle.dump((dict(T.v), dict(T.n)), open(os.path.join(W, 'mask_table.pkl'), 'wb'))
        pickle.dump(det, open(os.path.join(W, 'learn_bad.pkl'), 'wb'))
