"""dtp_keys.py - byte-class rules for DTP (type 7) words, keyed by the structure around the word, calibrated on the base
Xbox/PC pairs.  Complements dtp_audit.py (FP rule keyed by region fingerprint) with SLOT-ANCHORED keys (record arrays:
the key is the distance from the nearest preceding pointer slot) and a back-off over several key families.

Class of a word = permutation turning the Xbox (BE) bytes into the PC (LE) bytes: s32 | s16 (two u16) | raw | b2s16 (2 bytes
+ u16) | s16b2 (u16 + 2 bytes).  A key is RULED when >= MIN_N informative base samples (non-palindromic, class != none) exist and
the AND of their class masks is non-empty (rule = mask of classes consistent with ALL samples).  A DLC word is FLAGGED when
the class mask of (Xbox bytes -> our PC bytes) has no class in common with the rule; the correction is the rule class
applied to the Xbox bytes (only when every class of the rule gives the same bytes, else report-only).

Key families (most specific first, first RULED family decides the word):
  S1  (d, P/I mask of words slot-2 .. slot+8, target signature of the slot, shape)      d = words from the preceding pointer slot
  R   (dtp_audit.word_keys: offset in region, region mask, shape, parent slot)           region fingerprint
  C1  (shape + slot/shape of the two words before and after)                             pure local context
  S2  (d, mask slot..slot+4, shape)   S3 (d, shape)                                      coarse
Guards (fix_section): sizes equal; PC internal reloc layout == Xbox one (else analog / re-authored); slots, palindromic
words and class-none words untouched; words owned by the typed fixers (aidata records, animfx lists, model DTPs, STR/NODE0 spans)
are only reported; SoundPlex nodes are NOT excluded here but cross-checked after the build
(soundplex_nodes.py scan / soundplex_fix on the output must report 0 words).

Usage (cwd anywhere; python -I):
  tools/venv/bin/python -I tools/dtp_keys.py learn         -> work/ws/dtpkeys/rules.pkl (stats per family and fold)
  tools/venv/bin/python -I tools/dtp_keys.py heldout       (2-fold by DRM on REAL PC bytes: coverage, flags per family/combined)
  tools/venv/bin/python -I tools/dtp_keys.py scan [--set installed|DIRS] [--json OUT]
  tools/venv/bin/python -I tools/dtp_keys.py fix OUTDIR [--set ..] [names..]
Pipeline hook: fix_section(xd, xreloc, pd, sec_type=7, preloc=None) -> (bytes, log)
"""
import sys, os, struct, collections, bisect, pickle, zlib, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
import dtp_audit as A

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
WS = os.path.join(W, 'ws', 'dtpkeys')
RULES = os.path.join(WS, 'rules.pkl')
PERMS = A.PERMS; NAMES = A.NAMES; ALL = A.ALL
MIN_N = 20
DCAP = 64
# tiers: (min n, min distinct DTPs) a rule must reach to be used
GATE_TIER = (100, 8)
TIERS = {'T0': (20, 1), 'T1': (50, 3), 'T2': (100, 8), 'T3': (200, 16)}
FAMS = ('S1', 'R', 'C1', 'S2', 'S3')
GATE_ORDER = ('S1', 'R')          # hook default = the gating that was validated: families S1+R, tier T2 (n>=100, >=8 DTPs)
MAXD = 16                                   # max distance (words) from the slot anchor
# overlay actually installed in the VM (low -> high), CONVENTIONS.md + NOTES 'STATO INSTALLATO'
INSTALLED = A.INSTALLED + ['mods_fix20', 'chain_aim/mods_chainfix_min']

def shape(xw):
    return A.shape(xw)

# ------------------------------------------------------------------------------------------------------------ features
def prep(xd, rel):
    ptr = sorted(set(rel.pointer_offsets())); idl = set(rel.id_offsets())
    it = dict(rel.internal)
    n = len(xd) // 4
    tc = ['.'] * n
    for o in ptr:
        if o % 4 == 0 and o // 4 < n: tc[o // 4] = 'P'
    for o in idl:
        if o % 4 == 0 and o // 4 < n: tc[o // 4] = 'I'
    sh = [shape(xd[4 * i:4 * i + 4]) for i in range(n)]
    return ptr, idl, it, tc, sh

def tgsig(xd, it, o):
    t = it.get(o)
    if t is None: return 'x'
    if t + 4 > len(xd): return 'e'
    z = xd.find(b'\0', t, t + 64)
    if z - t >= 3 and z > 0 and all(32 <= c < 127 for c in xd[t:z]): return 's'
    return shape(xd[t:t + 4])

def keys_of(xd, rel):
    """[(offset, {family: key})] for every 4-aligned non-slot word of an Xbox DTP"""
    ptr, idl, it, tc, sh = prep(xd, rel)
    n = len(xd) // 4
    slots = set(ptr) | idl
    rk = dict(A.word_keys(xd, rel))
    sig = {}
    out = []
    for i in range(n):
        o = 4 * i
        if o in slots: continue
        ks = {}
        j = bisect.bisect_left(ptr, o) - 1
        if j >= 0:
            p = ptr[j]; d = (o - p) // 4
            if 0 < d <= MAXD and p % 4 == 0:
                pi = p // 4
                if p not in sig: sig[p] = tgsig(xd, it, p)
                m = ''.join(tc[k] if 0 <= k < n else '|' for k in range(pi - 2, pi + 8))
                ks['S1'] = ('S1', d, m, sig[p], sh[i])
                ks['S2'] = ('S2', d, m[2:7], sh[i])
                ks['S3'] = ('S3', d, sh[i])
        if o in rk: ks['R'] = ('R',) + rk[o]
        ctx = []
        for k in (i - 2, i - 1, i + 1, i + 2):
            ctx.append('|' if not 0 <= k < n else (tc[k] if tc[k] != '.' else sh[k]))
        ks['C1'] = ('C1', sh[i]) + tuple(ctx)
        out.append((o, ks))
    return out

# ----------------------------------------------------------------------------------------------------- learning
def fold(src): return zlib.crc32(src.encode()) & 1

def learn(verbose=True):
    """stats[f][key] = [n, and-mask, set of DTP ids (cap DCAP)] per fold -> rules[f][key] = (mask, n, d) merged over folds,
    folds[i][f][key] = (mask, n, d) learned on fold i only (held-out evaluation)"""
    stats = {f: {} for f in FAMS}
    ninf = 0
    for x, p, xb, pc, xr in A.base_pairs():
        fo = fold(xb['src']); xd, pd = xb['data'], pc['data']
        for o, ks in keys_of(xd, xr):
            c = A.cls(xd[o:o + 4], pd[o:o + 4])
            if c == ALL or c == 0: continue
            ninf += 1
            for f, k in ks.items():
                e = stats[f].get(k)
                if e is None: e = stats[f][k] = [0, ALL, set(), 0, ALL, set()]
                e[3 * fo] += 1; e[3 * fo + 1] &= c
                if len(e[3 * fo + 2]) < DCAP: e[3 * fo + 2].add(x)
    if verbose: print('informative base words', ninf, {f: len(s) for f, s in stats.items()})
    rules = {}; folds = [{}, {}]
    for f in FAMS:
        r = {}; r0 = {}; r1 = {}
        for k, (n0, a0, s0, n1, a1, s1) in stats[f].items():
            n = n0 + n1; a = a0 & a1
            if n >= MIN_N and a: r[k] = (a, n, len(s0 | s1))
            if n0 >= MIN_N and a0: r0[k] = (a0, n0, len(s0))
            if n1 >= MIN_N and a1: r1[k] = (a1, n1, len(s1))
        rules[f] = r; folds[0][f] = r0; folds[1][f] = r1
        if verbose: print('  family %-3s keys %8d ruled %7d (fold0 %d fold1 %d)' % (f, len(stats[f]), len(r), len(r0), len(r1)))
    pickle.dump(dict(rules=rules, folds=folds), open(RULES, 'wb'))
    return rules, folds

_RULES = None
def load_rules():
    global _RULES
    if _RULES is None:
        _RULES = pickle.load(open(RULES, 'rb'))['rules'] if os.path.exists(RULES) else learn()[0]
    return _RULES

def decide(ks, rules, order=FAMS, tier=(MIN_N, 1)):
    """first family with a rule reaching the tier (min n, min distinct DTPs) -> (family, rule mask, n, d)"""
    for f in order:
        k = ks.get(f)
        if k is not None:
            e = rules[f].get(k)
            if e and e[1] >= tier[0] and e[2] >= tier[1]: return f, e[0], e[1], e[2]
    return None, 0, 0, 0

def heldout(order_sets=None):
    d = pickle.load(open(RULES, 'rb')); folds = d['folds']
    orders = order_sets or {'S1': ('S1',), 'R': ('R',), 'C1': ('C1',), 'S2': ('S2',), 'S3': ('S3',), 'ALL': FAMS,
                            'S1+R': ('S1', 'R'), 'S1+R+C1': ('S1', 'R', 'C1')}
    inf = 0
    cells = [(o, t) for o in orders for t in TIERS]
    res = {c: collections.Counter() for c in cells}; ex = {c: collections.Counter() for c in cells}
    for x, p, xb, pc, xr in A.base_pairs():
        fo = fold(xb['src']); xd, pd = xb['data'], pc['data']; rl = folds[1 - fo]
        for o, ks in keys_of(xd, xr):
            c = A.cls(xd[o:o + 4], pd[o:o + 4])
            if c == ALL or c == 0: continue
            inf += 1
            for cell in cells:
                name, t = cell
                f, m, n, dd = decide(ks, rl, orders[name], TIERS[t])
                if not m: continue
                res[cell]['cov'] += 1
                if not c & m: res[cell]['flag'] += 1; ex[cell][x] += 1
    print('held-out 2-fold by DRM on real PC bytes; informative words', inf)
    for cell in cells:
        r = res[cell]
        print('  %-8s %-3s %-9s coverage %.3f  flagged %6d (rate %.1e) in %4d DTPs  top %s' % (
            cell[0], cell[1], TIERS[cell[1]], r['cov'] / inf, r['flag'], r['flag'] / max(r['cov'], 1), len(ex[cell]), ex[cell].most_common(3)))
    return res, ex

# --------------------------------------------------------------------------------------------------------- ownership
def owned_words(xd, rel, sec_type=7):
    """byte offsets of words handled by the typed fixers (aidata records, animfx lists, model DTPs, SoundPlex type-4 records,
    STR/NODE0): reported but never changed here.  -> set of word offsets, or None = whole DTP is owned (model DTP)"""
    own = set()
    if len(xd) >= 4 and struct.unpack_from('>I', xd, 0)[0] == 0x04c20453: return None
    try:
        import aidata_fix as AF
        for t in AF.detect(xd, rel): own.update(range(t, t + AF.SIZE, 4))
    except Exception: pass
    try:
        import animfx as AX
        w = AX.detect(xd, rel)
        if w is not None:
            recs, end = w
            for a, h, fr, sz in recs: own.update(range(a, a + sz, 4))
            own.update((0, end))
            own.update(AX.labels(xd, rel, w).keys())
    except Exception: pass
    try:
        for a, z, kind in A.string_spans(xd, rel): own.update(range(a - a % 4, z + 4, 4))
        if A.node0(xd, rel): own.add(0)
    except Exception: pass
    return own

# ---------------------------------------------------------------------------------------------------------- fixing
def _apply(xw, mask):
    """PC bytes for the rule mask: the common result of every class in the mask, else None"""
    res = {bytes(xw[j] for j in PERMS[NAMES[i]]) for i in range(5) if mask >> i & 1}
    return res.pop() if len(res) == 1 else None

def findings(xd, rel, pd, rules=None, order=FAMS, with_owned=True, tier=(MIN_N, 1)):
    """list of dicts for every word whose installed class contradicts the rule"""
    rules = rules or load_rules()
    own = owned_words(xd, rel) if with_owned else set()
    if own is None: return []
    out = []
    for o, ks in keys_of(xd, rel):
        xw, pw = xd[o:o + 4], pd[o:o + 4]
        c = A.cls(xw, pw)
        if c == ALL or c == 0: continue
        f, m, rn, rd = decide(ks, rules, order, tier)
        if not m or c & m: continue
        want = _apply(xw, m)
        out.append(dict(off=o, xbox=xw.hex(), pc=pw.hex(), want=want.hex() if want else None, fam=f, n=rn, d=rd, rule='/'.join(NAMES[i] for i in range(5) if m >> i & 1),
                        got='/'.join(NAMES[i] for i in range(5) if c >> i & 1), owned=o in own, key=repr(ks[f])[:120]))
    return out

def fix_section(xd, xreloc, pd, sec_type=7, preloc=None, rules=None, order=GATE_ORDER, tier=GATE_TIER):
    """-> (bytes, log) ; log = [(off, old, new, family, rule)] ; xreloc = Xbox (BE) reloc blob or parsed"""
    if len(pd) != len(xd) or sec_type != 7: return pd, []
    rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
    if preloc is not None and dict(R.parse(preloc, 'le').internal) != dict(rel.internal): return pd, []
    b = bytearray(pd); log = []
    for f in findings(xd, rel, pd, rules, order, tier=tier):
        if f['owned'] or f['want'] is None: continue
        o = f['off']; new = bytes.fromhex(f['want'])
        log.append((o, bytes(b[o:o + 4]), new, f['fam'], f['rule'])); b[o:o + 4] = new
    return bytes(b), log

def scan_file(rel, path, tier, order):
    xs = A.xsecs(rel)
    if xs is None: return []
    D = DW.read(open(path, 'rb').read(), 'le'); out = []
    for x, i in A.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or len(sec.data) != len(x['data']): continue
        if A.base_content(x): continue
        xr = R.parse(x['reloc'], 'be')
        if dict(xr.internal) != dict(R.parse(sec.reloc, 'le').internal): continue
        for f in findings(x['data'], xr, sec.data, None, order, tier=tier):
            f.update(file=rel, id=sec.id, xid=x['id'], src=os.path.relpath(path, W)); out.append(f)
    return out

def cmd_scan(dirs, tier, order, names=None):
    allf = []
    for rel, path in sorted(A.overlay(dirs, names).items()):
        allf += scan_file(rel, path, tier, order)
    return allf

def cmd_fix(out, dirs, tier, order, names):
    os.makedirs(out, exist_ok=True); md5 = []; logall = []
    for rel, path in sorted(A.overlay(dirs, names or None).items()):
        xs = A.xsecs(rel)
        if xs is None: continue
        raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); n = 0
        for x, i in A.section_pairs(xs, D):
            sec = D.sections[i]
            if x['type'] != 7 or A.base_content(x): continue
            nb, log = fix_section(x['data'], x['reloc'], sec.data, 7, sec.reloc, None, order, tier)
            if log:
                sec.data = nb; n += len(log)
                logall += [dict(file=rel, id=sec.id, off=l[0], old=l[1].hex(), new=l[2].hex(), fam=l[3], rule=l[4]) for l in log]
        if not n: continue
        o = D.write('le')
        if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
        D2 = DW.read(o, 'le'); D0 = DW.read(raw, 'le')
        assert len(D0.sections) == len(D2.sections) and D0.names == D2.names
        for a0, a2 in zip(D0.sections, D2.sections): assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
        md5.append('%s  %s' % (hashlib.md5(o).hexdigest(), rel)); print(rel, '<-', os.path.relpath(path, W), n, 'words')
    return md5, logall

if __name__ == '__main__':
    a = sys.argv[1:]
    def opt(name, d=None):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return d
    st = opt('--set'); js = opt('--json'); tn = opt('--tier', 'T0'); fam = opt('--fam', 'ALL')
    order = FAMS if fam == 'ALL' else tuple(fam.split('+')); tier = TIERS[tn]
    dirs = INSTALLED if st in (None, 'installed') else st.split(',')
    cmd = a[0]
    if cmd == 'learn': learn()
    elif cmd == 'heldout': heldout()
    elif cmd == 'scan':
        fs = cmd_scan(dirs, tier, order, set(a[1:]) or None)
        by = collections.Counter((f['file'], f['id'], f['owned']) for f in fs)
        print('findings', len(fs), 'DTPs', len(by))
        for (fi, i, ow), c in sorted(by.items()): print('  %-40s DTP %6d %s x%d' % (fi, i, 'owned' if ow else '', c))
        if js: json.dump(fs, open(js, 'w'), indent=0)
    elif cmd == 'fix':
        out = os.path.abspath(a[1])
        md5, lg = cmd_fix(out, dirs, tier, order, set(a[2:]))
        open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
        json.dump(lg, open(os.path.join(out, 'log.json'), 'w'), indent=0)
        with open(os.path.join(out, 'log.txt'), 'w') as fh:
            for l in lg: fh.write('%s DTP %d @%#x %s -> %s fam %s rule %s\n' % (l['file'], l['id'], l['off'], l['old'], l['new'], l['fam'], l['rule']))
