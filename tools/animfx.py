"""Anim EVENT-LIST DTPs ('animfx'): typed override for DTP (type 7) sections that hold an animation's frame-event list
(sound / fx / ... triggers), plus the structs the events point to (sound 'plex' nodes etc.).

Engine (tru.exe PC, Steam unpacked): anim player 0x43cc10 (this = anim controller, +0x24 anim, +0x34 EVENT LIST,
+0x44 callback 0x69a560) -> 0x43ce4b -> 0x5b26c0(.., list, cb, ..) walks
    list+0      u32  (0 in every base list)
    list+4..    records { u16 h, s16 frame, u8 b4 (+3 bytes), payload[(h >> 12) * 4] }   size = (h >> 12) * 4 + 8
                h: bits 0-1 kind, 2-3 flags (bit 2 = skip), 4-9 id, 10-11 channel, 12-15 payload words
                terminated by u16 h == 0xffff
and calls cb(.., msg 6, flags(h, b4), &payload, ..) for records whose frame is in the played window.
cb -> 0x5b9c40 -> switch(kind): kind 0 -> 0x5b99c0(payload): payload byte 0 == 0 -> sound: 0x5935d0(out, *(payload+4), 0.0)
reads [ptr+8].

Crash fix13 (2026-10-10, EIP 0x593659, read 0xbf800008): DLC DTP 20940 of dlc1_uo_adren_trap (event list of anim 4226)
was converted by the learned type-7 table with u32 swaps on the {u16 h, s16 frame} words (BE 2000000b -> 0b000020) and
on the terminator (ffff0000 -> 0000ffff): the walker mis-framed every record (size nibble 0), ran past the list into the
sound structs and passed float -1.0 (0xbf800000) as a sound pointer.  The table is keyed by (region label, offset); the
record offsets differ per list, so for DLC-new lists its classes are a mix (the second copy of 20940 in the same DRM got
u16 pairs on most headers but 61 records instead of 58, and b2s16 payload fields as s16).

This module:
  walk(xd)            Xbox (BE) list walk -> records or None (detector: word0 == 0, all h sane, ends on 0xffff)
  labels(xd, rel)     word offset -> structural key: ('H',) header, ('E', kind, size, off, channel[, kind-2 event type])
                      record words, ('T',) terminator,
                      regions reached through internal pointers -> (parent key, parent region word0 value, ...) + offset
  learn(pairs, idm)   per key: intersection of the classes (generic_learn.word_classes) seen on base Xbox/PC pairs
  fix(xd, rel, out)   record header words + terminator := u16 pairs (structural), every other word whose key has
                      one consistent class on base pairs := that class; pointers / id-ref words untouched.
Table: work/generic/animfx_table.pkl (python3 -I tools/animfx.py learn).  Validation: animfx.py validate.
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import generic_learn as G
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
TABLE = os.path.join(W, 'animfx_table.pkl')
PTR_SLOTS = {(0, 16, 12), (1, 24, 12)}          # payload pointer fields (100% internal relocs on the base pairs)

def walk(xd, e='>'):
    """records [(off, h, frame, size)] and terminator offset of an event list, or None if xd is not one."""
    if len(xd) < 8 or xd[:4] != b'\0\0\0\0': return None
    a = 4; out = []
    while a + 4 <= len(xd):
        h, fr = struct.unpack_from(e + 'Hh', xd, a)
        if h == 0xffff: return (out, a) if out else None
        sz = (h >> 12) * 4 + 8
        if fr < 0 or not 1 <= (h >> 12) <= 8 or a + sz > len(xd): return None     # payload-less 'records' = not a list
        out.append((a, h, fr, sz)); a += sz
    return None

def detect(xd, rel):
    """walk() + structural check: every learned pointer slot of the records carries an internal reloc."""
    w = walk(xd)
    if w is None: return None
    ptrs = set(rel.pointer_offsets())
    for a, h, fr, sz in w[0]:
        if (h & 3, sz, 12) in PTR_SLOTS and a + 12 not in ptrs: return None
    return w

def labels(xd, rel, w=None):
    """{word offset: key} for the list and every region reachable from it through internal pointers."""
    w = w or walk(xd)
    if w is None: return {}
    recs, end = w
    n = len(xd)
    it = dict(rel.internal)
    starts = sorted({0} | {t for t in it.values() if t < n})
    nxt = {s: (starts[k + 1] if k + 1 < len(starts) else n) for k, s in enumerate(starts)}
    lab = {0: ('H',)}
    for a, h, fr, sz in recs:
        sub = struct.unpack_from('>H', xd, a + 8)[0] if (h & 3) == 2 else None   # kind 2: payload u16 event type
        for o in range(0, sz, 4): lab[a + o] = ('E', h & 3, sz, o, (h >> 10) & 3) + ((sub,) if sub is not None and o else ())
    lab[end] = ('T',)
    q = collections.deque(o for o in sorted(lab) if o in it)
    region = {0: ('L',)}
    while q:
        o = q.popleft(); t = it[o]
        if t in region or t >= n or t % 4: continue
        ps = max(s for s in starts if s <= o)      # parent region start
        v0 = struct.unpack_from('>I', xd, ps)[0] if ps != 0 else None
        key = ('R', lab[o], v0)
        region[t] = key
        for w4 in range(t, min(nxt[t], n) // 4 * 4, 4):
            if w4 in lab: continue
            lab[w4] = (key, w4 - t)
            if w4 in it: q.append(w4)
    return lab

def word_classes(xw, pw, idm):
    cs = G.word_classes(xw, pw, idm)
    return None if cs is None else set(cs)

def pc_reauthored_drm(nm):
    """hook to drop evidence of PC re-authored DRMs (none needed: the only conflict, kind-2 payload word 8 = s16 vs s16b2,
    is explained by the payload's u16 event type (0x66 -> u16 + 2 bytes, 904/904), now part of the key)"""
    return False

def learn(pairs, idm, names=None):
    """{key: [n_evidence, set(classes) intersection]} over base pairs (Xbox list detected, PC list walks identically)."""
    T = {}
    stat = collections.Counter()
    for nm, (X, P) in pairs.items():
        if names is not None and nm not in names: continue
        if pc_reauthored_drm(nm): continue
        if X is None or not isinstance(P, tuple): continue
        ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
        for s in X[1]:
            if s['type'] != 7 or s['data'] is None: continue
            xd = s['data']; rel = R.parse(s['reloc'], 'be')
            w = detect(xd, rel)
            if w is None: continue
            pc = _pc_twin(s, ps)
            if pc is None: stat['no_pc'] += 1; continue
            pw = walk(pc['data'], '<')
            if pw is None or [(a, h, f) for a, h, f, _ in pw[0]] != [(a, h, f) for a, h, f, _ in w[0]] or pw[1] != w[1]:
                stat['pc_walk_differs'] += 1; continue
            stat['lists'] += 1
            skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            for o, k in labels(xd, rel, w).items():
                if o in skip or o + 4 > len(xd): continue
                cs = word_classes(xd[o:o + 4], pc['data'][o:o + 4], idm)
                if cs is None: continue
                e = T.get(k)
                if e is None: T[k] = [1, cs]
                else: e[0] += 1; e[1] &= cs
    return T, stat

def _pc_twin(s, ps):
    """PC section of the same position with identical size + reloc layout (else unique such section)"""
    def same(p):
        return p['size'] == s['size'] and p['reloc_bytes'] == s['reloc_bytes'] and \
            R.parse(p['reloc'], 'le').internal == R.parse(s['reloc'], 'be').internal
    c = [p for p in ps if p['i'] == s['i'] and same(p)]
    if c: return c[0]
    c = [p for p in ps if same(p)]
    return c[0] if len(c) == 1 else None

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
def fix(xd, rel, out, ids, T=None, min_n=1):
    """typed override on a converted DTP (bytearray out, LE); returns #words changed (0 if xd is not an event list)."""
    w = detect(xd, rel)
    if w is None or len(out) != len(xd): return 0
    T = table() if T is None else T
    recs, end = w
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    ch = 0
    def put(o, v):
        nonlocal ch
        if out[o:o + 4] != v: out[o:o + 4] = v; ch += 1
    for a, h, fr, sz in recs:
        put(a, struct.pack('<Hh', h, fr))                       # structural: {u16 h, s16 frame}
    put(end, struct.pack('<H', 0xffff) + xd[end + 2:end + 4][::-1])
    for o, k in labels(xd, rel, w).items():
        if o in skip or o + 4 > len(xd) or k in (('T',),) or (k[0] == 'E' and k[3] == 0): continue
        e = T.get(k)
        if e is None or e[0] < min_n: FIX_STATS['unseen' if e is None else 'thin'] += 1; continue
        c = choose(e)
        if c is None: FIX_STATS['ambiguous'] += 1; continue
        put(o, G.apply_word(xd[o:o + 4], c, ids))
    FIX_STATS['lists'] += 1; FIX_STATS['words'] += ch
    return ch

# ------------------------------------------------------------------------------------------------ CLI
def _pairs():
    return pickle.load(open(os.path.join(W, 'pairs.pkl'), 'rb'))

def _ids():
    import dlc_generic as DG, generic_store
    return DG.DlcIds(generic_store.load(), None)

class _BaseIds:
    """ids(t, v) with the base map only (validation on base pairs)"""
    def __init__(self, base): self.base = base
    def __call__(self, t, v): return self.base.get(t, {}).get(v, v)

def validate(pairs, idm):
    """2-fold by DRM name: learn on one half, apply fix() ON TOP OF the real PC bytes of the other half -> words changed
    = errors.  Also coverage: words of the held-out lists whose key was learned."""
    names = sorted(pairs); res = collections.Counter()
    ids = _BaseIds(idm)
    for fold in (0, 1):
        tr = {n for k, n in enumerate(names) if k % 2 != fold}
        T, _ = learn(pairs, idm, tr)
        for nm in names:
            if nm in tr: continue
            X, P = pairs[nm]
            if X is None or not isinstance(P, tuple): continue
            ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
            for s in X[1]:
                if s['type'] != 7 or s['data'] is None: continue
                rel = R.parse(s['reloc'], 'be')
                w = detect(s['data'], rel)
                if w is None: continue
                pc = _pc_twin(s, ps)
                if pc is None: continue
                buf = bytearray(pc['data'])
                n = fix(s['data'], rel, buf, ids, T)
                if pc_reauthored_drm(nm):
                    res['lara_lists'] += 1; res['lara_changed_words'] += n; continue
                res['lists'] += 1; res['changed_words'] += n; res['lists_changed'] += n > 0
                if n and res['ex'] < 10:
                    res['ex'] += 1
                    d = [o for o in range(0, len(buf) // 4 * 4, 4) if buf[o:o + 4] != pc['data'][o:o + 4]]
                    print('  held-out change', nm, s['id'], [(hex(o), s['data'][o:o + 4].hex(), pc['data'][o:o + 4].hex(), buf[o:o + 4].hex()) for o in d[:4]])
                lab = labels(s['data'], rel, w)
                skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
                for o, k in lab.items():
                    if o in skip or o + 4 > len(s['data']) or s['data'][o:o + 4] == s['data'][o:o + 4][::-1]: continue
                    res['nonpal_words'] += 1; res['covered'] += k in T and choose(T[k]) is not None
    return res

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'learn'
    pairs = _pairs(); ids = _ids()
    if cmd == 'learn':
        T, st = learn(pairs, ids.base)
        pickle.dump(T, open(TABLE, 'wb'))
        amb = sum(1 for e in T.values() if choose(e) is None)
        print('keys', len(T), 'ambiguous/conflicting', amb, dict(st))
    elif cmd == 'validate':
        print(dict(validate(pairs, ids.base)))
        # in-sample: all base type-7 sections (detected or not) on top of PC bytes -> must change nothing
        T = table(); bi = _BaseIds(ids.base); c = collections.Counter()
        for nm, (X, P) in pairs.items():
            if X is None or not isinstance(P, tuple): continue
            ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
            for s in X[1]:
                if s['type'] != 7 or s['data'] is None: continue
                pc = _pc_twin(s, ps)
                if pc is None: continue
                buf = bytearray(pc['data']); n = fix(s['data'], R.parse(s['reloc'], 'be'), buf, bi, T)
                p = 'lara_' if pc_reauthored_drm(nm) else ''
                c[p + 'dtps'] += 1; c[p + 'changed_dtps'] += n > 0; c[p + 'changed_words'] += n
        print('in-sample on PC bytes', dict(c))
