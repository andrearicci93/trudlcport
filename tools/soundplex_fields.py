"""soundplex_fields.py - field-format rule for DTP data words (SoundPlex trees etc.), calibrated on base Xbox/PC pairs.
Fixes float/small-int words left RAW (or taken as u16 pair) by the learned type-7 table.
Rule key of a non-pointer word = (offset k in its region, path of referrer records, value shape); a path element is
(SoundPlex node type of the pointing node 0..13 | -1, offset of the pointer inside the parent region, parent element...).
Depth 1..3, with/without value shape; most specific ruled key wins (order DL).  A key is RULED when >= MIN_N informative base
samples (words whose byte permutation is distinguishable) all agree on one permutation (s32|s16|raw|b2s16|s16b2).
Only class s32 rules are APPLIED, and only when the gate holds:
  FLOAT: Xbox BE float finite, 1e-4 <= |v| <= 1e6 and PC current LE float NOT in that range (raw / u16-pair left floats)
  MAG  : Xbox BE int 1..0xffff and PC current value >= 0x10000 (group/COUNT raw class)
and the corrected word (s32) reads plausible (same range / small int).
CLI (python -I tools/soundplex_fields.py ...):
  learn                      -> work/ws/fpfloat/sf_rules.pkl
  selftest                   base pairs: in-sample words changed on real PC bytes (must be 0) + held-out 2-fold flags/coverage
  scan [--set installed|DIR,..] [-v]
  fix OUTDIR [--set ..] [names..]    writes changed DRMs, md5.txt, log.txt (offset, before/after, rule)
Pipeline hook: fix_section(xd, xreloc, pd, rules=None) -> (bytes, log)
"""
import sys, os, struct, collections, bisect, pickle, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
import dtp_audit as A
from generic_type0 import shape

RULES = os.path.join(A.W, 'generic', 'sf_rules.pkl')
CONF = [(1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (3, 1), (1, 2)]       # (depth, use shape); 2 = big-array layer: offset>=0x400 collapsed (k=0x400 only for k>=0x400), shape F only
BIG = '--big' in sys.argv if __name__ == '__main__' else False      # opt-in (CLI only): big-array layer (73 real base words contradicted in-sample -> not a 0-change rule)
ORDER = [5, 4, 3, 2, 1, 0] + ([6] if BIG else [])
BIG_PURITY = 0.995; BIG_N = 1000
MIN_N = 20
SET = A.INSTALLED + ['mods_fix20', 'chain_aim/mods_chainfix_min']   # effective installed DLC1 (later wins), see CONVENTIONS
SKIP = {'g_pda.drm'}
MAG = False

def plaus(v): return math.isfinite(v) and 1e-4 <= abs(v) <= 1e6

def words(xd, rel, depth=3):
    slots = set(rel.pointer_offsets()); idsl = set(rel.id_offsets()); it = dict(rel.internal); both = slots | idsl
    tg = sorted({0} | {t for t in it.values() if t < len(xd)})
    refs = {}
    for o, t in sorted(it.items()): refs.setdefault(t, o)
    strw = set()
    for a, z, kd in A.string_spans(xd, rel):
        for q in range(a - a % 4, z + 1, 4): strw.add(q)
    memo = {}
    def start(o): return tg[bisect.bisect_right(tg, o) - 1]
    def rkey(s, d):
        m = memo.get((s, d))
        if m is not None: return m
        o = refs.get(s)
        if o is None: r = ('root', len(xd) if s == 0 else -1)
        else:
            ps = start(o)
            w = struct.unpack_from('>I', xd, o - 4)[0] if o >= 4 and (o - 4) not in both else 99
            r = (w if w <= 13 else -1, o - ps, rkey(ps, d - 1) if d > 1 else None)
        memo[s, d] = r; return r
    cur = -1; ks = None
    for o in range(0, len(xd) - 3, 4):
        if o in both or o in strw: continue
        s = start(o)
        if s != cur: cur = s; ks = tuple(rkey(s, d) for d in range(1, depth + 1))
        yield o, min(o - s, 0x400), ks, shape(xd[o:o + 4])

def keys_of(k, ks, sh): return [(k, ks[d - 1], sh if us == 1 else 0) if us < 2 else ((k, ks[0], 'F') if (k >= 0x400 and sh == 'F') else None) for d, us in CONF]

def mkrules(stat):
    out = []
    for ci, d in enumerate(stat):
        r = {}
        for k, v in d.items():
            if k is None: continue
            i = max(range(5), key=lambda j: v[j + 1])
            if ci == 6 and v[0] >= BIG_N:
                if v[i + 1] >= BIG_PURITY * v[0] and i == 0: r[k] = i; continue
            if v[0] >= MIN_N and v[i + 1] == v[0]: r[k] = i
        out.append(r)
    return out

def learn():
    st = [[collections.defaultdict(lambda: [0] * 6) for _ in CONF] for _ in range(2)]
    n = 0
    for x, p, xb, pc, xr in A.base_pairs():
        f = A.fold(xb['src']); xd = xb['data']; pd = pc['data']
        for o, k, ks, sh in words(xd, xr):
            c = A.cls(xd[o:o + 4], pd[o:o + 4])
            if c == A.ALL or c == 0: continue
            n += 1
            for ci, key in enumerate(keys_of(k, ks, sh)):
                if key is None: continue
                v = st[f][ci][key]; v[0] += 1
                for i in range(5):
                    if c >> i & 1: v[i + 1] += 1
    tot = []
    for ci in range(len(CONF)):
        t = collections.defaultdict(lambda: [0] * 6)
        for f in (0, 1):
            for k, v in st[f][ci].items():
                for i in range(6): t[k][i] += v[i]
        tot.append(t)
    d = dict(rules=mkrules(tot), folds=[mkrules(st[0]), mkrules(st[1])], informative=n)
    os.makedirs(os.path.dirname(RULES), exist_ok=True); pickle.dump(d, open(RULES, 'wb'))
    print('informative base words', n, 'ruled keys per conf', [len(r) for r in d['rules']])
    return d

_D = None
def load():
    global _D
    if _D is None: _D = pickle.load(open(RULES, 'rb')) if os.path.exists(RULES) else learn()
    return _D

def lookup(rules, k, ks, sh):
    for ci in ORDER:
        kk = keys_of(k, ks, sh)[ci]
        r = rules[ci].get(kk) if kk is not None else None
        if r is not None: return r, ci
    return None, None

def gate(xw, pw):
    """-> 'FLOAT' | 'MAG' | None for an s32-ruled word whose PC bytes are not s32"""
    want = xw[::-1]
    if pw == want or (all(32 <= c < 127 for c in xw) and sum(chr(c).isalpha() for c in xw) >= 3): return None   # text words ('Dice','HOV]') are never numbers
    fx = struct.unpack('>f', xw)[0]; fp = struct.unpack('<f', pw)[0]; fw = struct.unpack('<f', want)[0]
    if plaus(fx) and plaus(fw) and not plaus(fp): return 'FLOAT'
    xv = struct.unpack('>I', xw)[0]; pv = struct.unpack('<I', pw)[0]
    if 1 <= xv <= 0xffff and pv >= 0x10000: return 'MAG'
    return None

def fix_section(xd, xreloc, pd, rules=None, preloc=None):
    """-> (new pc bytes, [(off, old hex, new hex, 'KIND:s32:conf')])"""
    if len(xd) != len(pd): return pd, []
    rules = rules or load()['rules']
    rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
    if preloc is not None and dict(R.parse(preloc, 'le').internal) != dict(rel.internal): return pd, []
    b = bytearray(pd); log = []
    for o, k, ks, sh in words(xd, rel):
        xw = bytes(xd[o:o + 4]); pw = bytes(pd[o:o + 4])
        if xw == pw[::-1] or xw == b'\0\0\0\0' or A.cls(xw, pw) == 0: continue   # PC word must be a byte permutation of the Xbox word
        r, ci = lookup(rules, k, ks, sh)
        if r != 0: continue
        g = gate(xw, pw)
        if g == 'MAG' and not MAG: g = None     # MAG: 170 held-out base flags (u16/flag words) -> report only (soundplex_nodes/fix handle COUNT/group)
        if g:
            log.append((o, pw.hex(), xw[::-1].hex(), '%s:s32:c%d' % (g, ci))); b[o:o + 4] = xw[::-1]
    return bytes(b), log

def selftest():
    d = load(); n = c = 0; held = collections.Counter(); cov = tot = 0; fl = []
    for x, p, xb, pc, xr in A.base_pairs():
        xd = xb['data']; pd = pc['data']; f = A.fold(xb['src'])
        _, log = fix_section(xd, xr, pd, d['rules']); n += 1; c += len(log)
        _, lh = fix_section(xd, xr, pd, d['folds'][1 - f])
        if lh: held['words'] += len(lh); held['dtps'] += 1; fl += [(x,) + l for l in lh[:2]]
        for o, k, ks, sh in words(xd, xr):
            xw = xd[o:o + 4]; pw = pd[o:o + 4]
            if not plaus(struct.unpack('>f', xw)[0]) or xw == xw[::-1]: continue
            cc = A.cls(xw, pw)
            if cc == 0: continue
            tot += 1
            if lookup(d['folds'][1 - f], k, ks, sh)[0] is not None: cov += 1
    print('base pairs %d: words changed on REAL PC bytes with full rules (in-sample) = %d' % (n, c))
    print('held-out 2-fold by DRM: gated flags %d words in %d DTPs %s' % (held['words'], held['dtps'], fl[:6]))
    print('float-looking base words (informative-or-not, permutation-class) %d, covered by a held-out rule %d (%.3f)' % (tot, cov, cov / max(tot, 1)))
    return c

def run(dirs, names=None, write=None):
    import dtpid_sweep as DS
    d = load(); allf = []; md5 = []; files = A.overlay(dirs, names)
    for rel, path in sorted(files.items()):
        if os.path.basename(rel) in SKIP: continue
        xs = A.xsecs(rel)
        if xs is None: continue
        raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logs = []
        for x, i in A.section_pairs(xs, D):
            sec = D.sections[i]
            if x['type'] != 7 or len(sec.data) != len(x['data']) or A.base_content(x): continue
            nb, log = fix_section(x['data'], x['reloc'], sec.data, d['rules'], preloc=sec.reloc)
            if log: logs += [(sec.id,) + l for l in log]; sec.data = nb if write else sec.data
        for l in logs: allf.append((rel, os.path.relpath(path, A.W)) + l)
        if write and logs:
            o = D.write('le')
            if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
            dst = os.path.join(write, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
            D2 = DW.read(o, 'le'); again = 0
            for x, i in A.section_pairs(xs, D2):
                s2 = D2.sections[i]
                if x['type'] == 7 and len(s2.data) == len(x['data']) and not A.base_content(x):
                    again += len(fix_section(x['data'], x['reloc'], s2.data, d['rules'], preloc=s2.reloc)[1])
            D0 = DW.read(raw, 'le'); nd = 0
            okw = collections.defaultdict(set)
            for l in logs: okw[l[0]].update(range(l[1], l[1] + 4))
            assert D0.names == D2.names and len(D0.sections) == len(D2.sections), rel
            for a0, a2 in zip(D0.sections, D2.sections):
                assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags) and len(a0.data) == len(a2.data), rel
                for j in range(len(a0.data)):
                    if a0.data[j] != a2.data[j]:
                        nd += 1; assert j in okw[a0.id], (rel, a0.id, hex(j))      # only bytes of logged words may change
            md5.append('%s  %s' % (hashlib.md5(o).hexdigest(), rel))
            print(rel, 'words', len(logs), 'recheck', again, 'bytes differing', nd)
    return allf, md5

if __name__ == '__main__':
    a = sys.argv[1:]
    def opt(n, dflt=None):
        if n in a: i = a.index(n); v = a[i + 1]; del a[i:i + 2]; return v
        return dflt
    if '--big' in a: a.remove('--big')
    st = opt('--set'); verbose = '-v' in a
    if verbose: a.remove('-v')
    dirs = SET if st in (None, 'installed') else st.split(',')
    cmd = a[0]
    if cmd == 'learn': learn()
    elif cmd == 'selftest': selftest()
    elif cmd == 'scan':
        allf, _ = run(dirs, set(a[1:]) or None)
        byk = collections.Counter(l[5].split(':')[0] for l in allf)
        print('TOTAL words', len(allf), dict(byk), 'DTPs', len({(l[0], l[2]) for l in allf}), 'files', len({l[0] for l in allf}))
        for k, v in sorted(collections.Counter((l[0], l[2]) for l in allf).items()): print('  %3d %s DTP %d' % (v[1] if False else v, k[0], k[1]))
        if verbose:
            for l in allf: print('   %s DTP %d @%#x %s -> %s %s' % (l[0], l[2], l[3], l[4], l[5], l[6]))
    elif cmd == 'fix':
        out = os.path.abspath(a[1]); os.makedirs(out, exist_ok=True)
        allf, md5 = run(dirs, set(a[2:]) or None, write=out)
        open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
        with open(os.path.join(out, 'log.txt'), 'w') as f:
            for l in allf: f.write('%s\tsrc=%s\tDTP %d\t@%#x\t%s\t->\t%s\t%s\n' % l)
        print('words', len(allf), 'files', len(md5), 'wrote md5.txt log.txt in', out)
