"""AI COMBAT-DATA records in level DTPs ('aidata'): typed override for the 0x390-byte enemy AI records that level unit DTPs
carry (one per enemy archetype placed in the level: small spiders, giant spider, ...).

Crash glitchfix_run (2026-10-10, dlc_caverns after 'small spiders', EIP 0x54df84, read 0x93076f28):
  AI brain object (static 0xd09ff0 for the spider) -> 0x618ee0(obj, mode 0..3) jump table 'melee'/'melee1'/'melee2'/...
  -> 0x618bc0(obj, rec = *(obj+0x104) + 0x1f4/0x20c/0x224/0x23c, name) -> if rec[+0x10] == 0: 0x594ff0 -> 0x54df80(id = rec[0])
  = DTP table lookup  mov eax,[eax*4 + 0xc36f28]  WITHOUT bounds check (the 'Out of range DTP Data ID!' check, < 0x8000,
  only exists on insert 0x54dd10).  rec[0] was 0x24910000: Xbox DTP id 0x2491 (9361) converted as a u16 PAIR.
  obj+0x104 = 0x2049cf30 = DTP 20872 of dlc_caverns.drm + 0x5530 (DTP loaded at 0x20497a00).
Record layout (base pairs, 450 instances in 41 DRMs, 0 conflicts): u32 0x0d @+0 (signature), internal pointers @+0x28
(always), +0x34/+0x38 (+0x40..0x50 sometimes), then 24-byte entries {u32 DTP id, u32 count/kind, ...} with the DTP id at
+0x8c + 0x18*k (k = 0..32 up to +0x374) WITHOUT id-ref relocs: PC stores ids(7, xbox id) as a plain LE u32
(e.g. small spider attack DTPs Xbox 9357..9362 -> PC 8985..8990).  Every other word with evidence is an s32 (u32 swap),
+0x0c / +0x3c are byte data ('raw').
The learned type-7 table (keyed by region label + offset) gave this DLC-new level DTP a mix of u16-pair swaps (wrong
counts AND ids, -> the crash) and u32 swaps without the id remap (wrong DTP: PC 9358 is a naga DTP).

  detect(xd, rel)       -> record start offsets: internal-reloc target t, BE u32 13 at t, internal pointer at t+0x28,
                           no internal target inside (t, t+0x390), t+0x390 <= size
  learn(pairs, idm)     -> {offset: [n_evidence, set(classes)]} intersection over base Xbox/PC pairs
  fix(xd, rel, out, ids)-> words changed (pointers / id-ref words untouched; offsets without base evidence untouched)
CLI: python3 -I tools/aidata_fix.py learn | validate | scan DIR[,DIR..] | patch OUTDIR SRCDIR[,SRCDIR..] name.drm ..
Table: work/generic/aidata_table.pkl.
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
TABLE = os.path.join(W, 'aidata_table.pkl')
SIZE = 0x390
SIG = 13

def detect(xd, rel):
    ints = rel.internal
    if not ints: return []
    tg = sorted({b for a, b in ints}); src = {a for a, b in ints}
    out = []
    for k, t in enumerate(tg):
        if t + SIZE > len(xd) or struct.unpack_from('>I', xd, t)[0] != SIG: continue
        if t + 0x28 not in src: continue
        if k + 1 < len(tg) and tg[k + 1] < t + SIZE: continue
        out.append(t)
    return out

def _pc_twin(s, ps):
    def same(p):
        return p['size'] == s['size'] and p['reloc_bytes'] == s['reloc_bytes'] and \
            R.parse(p['reloc'], 'le').internal == R.parse(s['reloc'], 'be').internal
    c = [p for p in ps if p['i'] == s['i'] and same(p)]
    if c: return c[0]
    c = [p for p in ps if same(p)]
    return c[0] if len(c) == 1 else None

def _iter_pairs(pairs, names=None):
    for nm, (X, P) in pairs.items():
        if names is not None and nm not in names: continue
        if X is None or not isinstance(P, tuple): continue
        ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
        for s in X[1]:
            if s['type'] != 7 or s['data'] is None: continue
            rel = R.parse(s['reloc'], 'be')
            st = detect(s['data'], rel)
            if not st: continue
            pc = _pc_twin(s, ps)
            yield nm, s, rel, st, pc

def learn(pairs, idm, names=None):
    T = {}; stat = collections.Counter()
    for nm, s, rel, st, pc in _iter_pairs(pairs, names):
        if pc is None: stat['no_pc'] += 1; continue
        skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
        for t in st:
            if struct.unpack_from('<I', pc['data'], t)[0] != SIG: stat['pc_sig_differs'] += 1; continue
            stat['records'] += 1
            for w in range(0, SIZE, 4):
                if t + w in skip: continue
                cs = G.word_classes(s['data'][t + w:t + w + 4], pc['data'][t + w:t + w + 4], idm)
                if cs is None: continue
                e = T.get(w)
                if e is None: T[w] = [1, set(cs)]
                else: e[0] += 1; e[1] &= set(cs)
    return T, stat

_T = None
def table():
    global _T
    if _T is None:
        _T = pickle.load(open(TABLE, 'rb')) if os.path.exists(TABLE) else {}
    return _T

def choose(e):
    n, cs = e
    if not cs: return None
    basic = [c for c in G.BASIC if c in cs]
    if basic: return basic[0]
    return sorted(cs)[0] if len(cs) == 1 else None

FIX_STATS = collections.Counter()
def fix(xd, rel, out, ids, T=None):
    """typed override on a converted DTP (bytearray out, LE); returns #words changed."""
    if len(out) != len(xd): return 0
    st = detect(xd, rel)
    if not st: return 0
    T = table() if T is None else T
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    ch = 0
    for t in st:
        FIX_STATS['records'] += 1
        for w in range(0, SIZE, 4):
            o = t + w
            if o in skip: continue
            xw = xd[o:o + 4]
            e = T.get(w)
            if e is None:
                if xw != xw[::-1]: FIX_STATS['unseen_nonpal'] += 1
                continue
            c = choose(e)
            if c is None: FIX_STATS['ambiguous'] += 1; continue
            v = G.apply_word(xw, c, ids)
            if out[o:o + 4] != v: out[o:o + 4] = v; ch += 1
    FIX_STATS['words'] += ch
    return ch

# ------------------------------------------------------------------------------------------------ CLI
def _pairs():
    return pickle.load(open(os.path.join(W, 'pairs.pkl'), 'rb'))

def _ids():
    import dlc_generic as DG, generic_store
    return DG.DlcIds(generic_store.load(), None)

class _BaseIds:
    def __init__(self, base): self.base = base
    def __call__(self, t, v): return self.base.get(t, {}).get(v, v)

def validate(pairs, idm):
    """2-fold by DRM: learn on one half, apply fix() ON TOP OF the real PC bytes of the other half (changed words = errors),
    and from a naive all-s32 conversion of the Xbox bytes (exact words vs PC)."""
    names = sorted(pairs); res = collections.Counter(); ids = _BaseIds(idm)
    for fold in (0, 1):
        tr = {n for k, n in enumerate(names) if k % 2 != fold}
        T, _ = learn(pairs, idm, tr)
        for nm, s, rel, st, pc in _iter_pairs(pairs, set(names) - tr):
            if pc is None: continue
            buf = bytearray(pc['data'])
            n = fix(s['data'], rel, buf, ids, T)
            res['records'] += len(st); res['changed_words_on_pc'] += n
            if n and res['ex'] < 10:
                res['ex'] += 1
                d = [o for o in range(0, len(buf) // 4 * 4, 4) if buf[o:o + 4] != pc['data'][o:o + 4]]
                print('  held-out change', nm, s['id'], [(hex(o), s['data'][o:o + 4].hex(), pc['data'][o:o + 4].hex(), buf[o:o + 4].hex()) for o in d[:4]])
            naive = bytearray(len(s['data']))
            for o in range(0, len(naive) // 4 * 4, 4): naive[o:o + 4] = s['data'][o:o + 4][::-1]
            fix(s['data'], rel, naive, ids, T)
            skip = set(rel.pointer_offsets())
            for t in st:
                for w in range(0, SIZE, 4):
                    if t + w in skip: continue
                    res['words'] += 1; res['exact'] += naive[t + w:t + w + 4] == pc['data'][t + w:t + w + 4]
    return res

def _load_le(path):
    import drm_write as DW
    return DW.read(open(path, 'rb').read(), 'le')

def patch_file(raw_old, xs, ids):
    """apply fix() to every DTP of an installed converted DRM (raw bytes); returns (new raw or None, report)."""
    import drm_write as DW
    D = DW.read(raw_old, 'le')
    pool = collections.defaultdict(list)
    for o in D.sections: pool[o.type, o.id].append(o)
    rep = []
    for s in xs:
        if s['type'] != 7: continue
        rel = R.parse(s['reloc'], 'be')
        st = detect(s['data'], rel)
        lst = pool.get((7, ids(7, s['id'])))
        if not lst: continue
        o = lst.pop(0)
        if not st: continue
        b = bytearray(o.data)
        n = fix(s['data'], rel, b, ids)
        rep.append((s['id'], o.id, [hex(t) for t in st], n))
        if n: o.data = bytes(b)
    if not any(r[3] for r in rep): return None, rep
    data = D.write('le')
    if raw_old[:4] == b'CDRM': data = DW.cdrm_encode(data, 'le')
    return data, rep

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'learn'
    if cmd == 'learn':
        ids = _ids(); T, st = learn(_pairs(), ids.base)
        pickle.dump(T, open(TABLE, 'wb'))
        print('offsets', len(T), 'ambiguous/conflicting', sum(1 for e in T.values() if choose(e) is None), dict(st))
        print('id32:7 offsets', [hex(w) for w, e in sorted(T.items()) if choose(e) == 'id32:7'])
    elif cmd == 'validate':
        ids = _ids(); pairs = _pairs()
        print('2-fold', dict(validate(pairs, ids.base)))
        T = table(); bi = _BaseIds(ids.base); c = collections.Counter()
        for nm, (X, P) in pairs.items():          # in-sample: every base DTP on top of its PC bytes must stay unchanged
            if X is None or not isinstance(P, tuple): continue
            ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
            for s in X[1]:
                if s['type'] != 7 or s['data'] is None: continue
                rel = R.parse(s['reloc'], 'be')
                if not detect(s['data'], rel): continue
                pc = _pc_twin(s, ps)
                if pc is None: c['no_pc'] += 1; continue
                buf = bytearray(pc['data']); n = fix(s['data'], rel, buf, bi, T)
                c['dtps'] += 1; c['changed_dtps'] += n > 0; c['changed_words'] += n
        print('in-sample on PC bytes', dict(c))
    elif cmd in ('scan', 'patch'):
        from drm import cdrm_decode, sections_with_data
        from convert_dlc import raw_dlc
        ids = _ids()
        if cmd == 'scan':
            dirs = sys.argv[2].split(','); out_dir = None
            names = sorted({os.path.relpath(os.path.join(r, f), d) for d in dirs for r, _, fs in os.walk(d) for f in fs if f.endswith('.drm')})
        else:
            out_dir, dirs, names = sys.argv[2], sys.argv[3].split(','), sys.argv[4:]
        for name in names:
            path = next((os.path.join(d, name) for d in dirs if os.path.exists(os.path.join(d, name))), None)
            if path is None: print(name, 'not found'); continue
            raw, _ = raw_dlc(name.replace('/', '\\'))
            if raw is None: raw, _ = raw_dlc(os.path.basename(name))
            if raw is None: continue
            _, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
            old = open(path, 'rb').read()
            new, rep = patch_file(old, xs, ids)
            if rep: print(name, 'from', path, rep)
            if out_dir and new is not None:
                op = os.path.join(out_dir, name); os.makedirs(os.path.dirname(op), exist_ok=True)
                open(op, 'wb').write(new)
        print(dict(FIX_STATS))
