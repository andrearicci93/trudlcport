"""dtp_audit.py - offline audit of the Xbox(BE)->PC(LE) conversion of DLC DRM data sections (DTP type 7, plus strings in
types 0/7/8), calibrated on the base-game Xbox/PC pairs.  Purpose: find 'word converted with the wrong byte permutation'
defects WITHOUT playing (cases so far: SoundPlex COUNT raw, aidata, event-list headers, 'chain_free' -> 'hcian_free').

Every 4-byte word is classified by the permutation that turns the Xbox bytes into our PC bytes
(s32 | s16 = two u16 | raw | b2s16 = 2 bytes + u16 | s16b2 = u16 + 2 bytes; none = id remap / other).
Detectors (all compare against the Xbox source of the same DRM, paired by section index / remapped DTP id):
  STR  (fixable)  NUL-terminated identifier string (>= 4 chars of [A-Za-z0-9_ .-/\\:], >= 2 letters, short ones >= 3
                  lowercase) at an INTERNAL POINTER TARGET must be byte-identical (raw) on PC, whole 4-byte words included.
                  Base pairs (types 0/7/8): 14473 spans 0 differ; whole-word ranges 13971, 0 differ.
  NODE0 (fixable) word 0 of a DTP = {u32 1..13, ptr at +4} (inferred: SoundPlex root node) is s32. Base 1914/1914.
  STR8 (fixable)  same, not pointer-referenced: 4-aligned run after a NUL, >= 8 chars, >= 3 letters.  Base: 10466, 0 differ.
  FP   (report)   local-structure fingerprint rule: key = (offset in region (region = from the nearest preceding internal
                  pointer target), pointer/id-slot mask of the region's first 16 words, value shape of the Xbox word,
                  parent slot (offset + mask of the region that points here)).  A key is RULED when >= MIN_N informative base
                  samples all agree on one permutation.  A DLC word whose permutation (not id/other) contradicts the rule is
                  reported.  Held-out (2-fold by DRM, on REAL PC bytes): coverage ~60%, false-flag rate ~1.7e-4 per covered
                  word -> candidates for review, never auto-fixed.
  MAG  (report)   subset of FP where the contradiction turns a small Xbox integer (1..0xffff) into a PC value >= 0x10000
                  (the 'COUNT raw -> 256 MB' / 'group 0x2d -> 0x2d000000' class).
Usage (dirs relative to work/, overlay low -> high):
  tools/venv/bin/python -I tools/dtp_audit.py learn                       -> work/generic/dtp_audit_rules.pkl
  tools/venv/bin/python -I tools/dtp_audit.py validate                    (base FP of STR/STR8/FP, fix on real PC = 0 change)
  tools/venv/bin/python -I tools/dtp_audit.py scan [--set installed|DIR,DIR..] [--json OUT] [-v]
  tools/venv/bin/python -I tools/dtp_audit.py controls                    (historical defects must be flagged)
  tools/venv/bin/python -I tools/dtp_audit.py fix OUTDIR [--set ..] [names..]   (STR/STR8 only; writes changed DRMs + md5)
Pipeline hook: fix_strings(xd, xreloc, pd, sec_type) -> (bytes, log)  (dlc_generic.convert_drm, after SoundPlex).
"""
import sys, os, struct, collections, bisect, pickle, zlib, re, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
RULES = os.path.join(W, 'generic', 'dtp_audit_rules.pkl')
INSTALLED = ['vm_mods_expected', 'mods_fix12', 'mods_fix14', 'mods_glitchfix', 'mods_next', 'mods_fix16', 'mods_current',
             'mods_current_webs', 'mods_fix18', 'mods_fix18_awf_extra']
PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
NAMES = list(PERMS)
ALL = (1 << len(PERMS)) - 1
MIN_N = 20
STR_CH = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_ .-/\\:')
LETTERS = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
RX8 = re.compile(rb'[A-Za-z0-9_ .\-/\\:]{8,}\x00')

def cls(xw, pw):
    m = 0
    for i, p in enumerate(PERMS.values()):
        if bytes(xw[j] for j in p) == pw: m |= 1 << i
    return m

def shape(xw):
    from generic_type0 import shape as sh
    return sh(xw)

# ------------------------------------------------------------------------------------------------------------ strings
def string_spans(xd, rel):
    """[(start, nul, kind)] of identifier strings in Xbox data. kind 'STR' = pointer target, 'STR8' = unreferenced run"""
    slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    tg = {t for _, t in rel.internal if t < len(xd)}
    out = {}
    for t in tg:
        z = xd.find(b'\0', t, t + 256)
        if z < 0 or z - t < 4: continue
        s = xd[t:z]
        if not all(c in STR_CH for c in s) or sum(c in LETTERS for c in s) < 2: continue
        if len(s) < 6 and sum(97 <= c <= 122 for c in s) < 3: continue     # short: >= 3 lowercase (no 'F rZG' float pairs)
        if any(q in slots for q in range(t - t % 4, z + 1, 4)): continue
        out[t] = (t, z, 'STR')
    for m in RX8.finditer(xd):
        a, z = m.start(), m.end() - 1
        if a % 4 or a in out or (a > 0 and xd[a - 1] != 0): continue
        if sum(c in LETTERS for c in xd[a:z]) < 3: continue
        if any(q in slots for q in range(a, z + 1, 4)): continue
        out[a] = (a, z, 'STR8')
    return sorted(out.values())

FIX_KINDS = ('STR', 'NODE0')       # applied by fix_strings / the pipeline; STR8 is report-only (5 base samples)

def node0(xd, rel):
    """DTP whose word 0 is a node type {u32 1..13, ptr} (SoundPlex root read as u32 by walker 0x5920b0): offset 0 must be
    s32. Base pairs: 1914 such DTPs, PC s32 in 1914."""
    if len(xd) < 8: return False
    slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    it = dict(rel.internal)
    return 0 not in slots and 4 in it and 1 <= struct.unpack_from('>I', xd, 0)[0] <= 13

def fix_strings(xd, xreloc, pd, sec_type=7, kinds=FIX_KINDS, preloc=None):
    """restore Xbox bytes of identifier strings (raw on PC) + NODE0 (s32); xreloc = Xbox (BE) reloc blob. -> (bytes, log)
    preloc = our PC (LE) reloc blob: when given, sections whose internal pointer layout differs from the Xbox one (analog /
    PC re-authored layouts, e.g. the shifted goo fx block) are left alone."""
    if len(pd) != len(xd) or sec_type not in (0, 7, 8): return pd, []
    rel = R.parse(xreloc, 'be') if isinstance(xreloc, (bytes, bytearray)) else xreloc
    if preloc is not None and dict(R.parse(preloc, 'le').internal) != dict(rel.internal): return pd, []
    b = bytearray(pd); log = []
    slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    for a, z, kind in string_spans(xd, rel):
        if kind not in kinds: continue
        e = z + 1
        if a % 4 == 0:                      # whole 4-byte words (bytes after the NUL too): base 13971 spans, 0 differ
            e2 = z - z % 4 + 4
            if e2 <= len(xd) and not any(q in slots for q in range(a, e2, 4)): e = e2
        if b[a:e] != xd[a:e]:
            log.append((kind, a, bytes(b[a:e]), bytes(xd[a:e])))
            b[a:e] = xd[a:e]
    if 'NODE0' in kinds and sec_type == 7 and node0(xd, rel) and b[0:4] != xd[3::-1]:
        log.append(('NODE0', 0, bytes(b[0:4]), xd[3::-1])); b[0:4] = xd[3::-1]
    return bytes(b), log

# ------------------------------------------------------------------------------------------------------- fingerprints
def word_keys(xd, rel):
    """[(offset, key)] for every 4-aligned non-slot word of an Xbox DTP"""
    slots = set(rel.pointer_offsets()); idsl = set(rel.id_offsets())
    it = dict(rel.internal)
    tg = sorted({0} | {t for t in it.values() if t < len(xd)}); tgs = set(tg)
    parent = {}
    for o, t in sorted(it.items()): parent.setdefault(t, o)
    def mask(s):
        m = []
        for k in range(16):
            q = s + 4 * k
            if q >= len(xd) or (k and q in tgs): break
            m.append('P' if q in slots else 'I' if q in idsl else '.')
        return ''.join(m)
    rc = {}; out = []
    for o in range(0, len(xd) - 3, 4):
        if o in slots or o in idsl: continue
        s = tg[bisect.bisect_right(tg, o) - 1]
        if s not in rc:
            po = parent.get(s)
            pk = None
            if po is not None:
                ps = tg[bisect.bisect_right(tg, po) - 1]; pk = (po - ps, mask(ps))
            rc[s] = (mask(s), pk)
        m, pk = rc[s]
        if pk is None: pk = ('root', len(xd) if s == 0 else -1)   # unreferenced region: the DTP size is part of the key
        out.append((o, (min(o - s, 0x400), m, shape(xd[o:o + 4]), pk)))
    return out

def base_pairs():
    import dtpid_sweep as DS
    st, ids = DS.ctx()
    for (t, x), xb in st['xb_store'].items():
        if t != 7: continue
        p = ids.base[7].get(x); pc = st['pc_store'].get((7, p)) if p is not None else None
        if pc is None or len(pc['data']) != len(xb['data']): continue
        xr = R.parse(xb['reloc'], 'be')
        if dict(xr.internal) != dict(R.parse(pc['reloc'], 'le').internal): continue
        yield x, p, xb, pc, xr

def fold(src): return zlib.crc32(src.encode()) & 1

def make_rules(stat, n_min=MIN_N):
    r = {}
    for k, v in stat.items():
        if v[0] < n_min: continue
        i = max(range(5), key=lambda j: v[j + 1])
        if v[i + 1] == v[0]: r[k] = i
    return r

def learn():
    stats = [collections.defaultdict(lambda: [0] * 6) for _ in range(2)]
    samples = []
    for x, p, xb, pc, xr in base_pairs():
        f = fold(xb['src']); xd, pd = xb['data'], pc['data']
        for o, k in word_keys(xd, xr):
            c = cls(xd[o:o + 4], pd[o:o + 4])
            if c == ALL or c == 0: continue           # palindromic (no evidence) / not a permutation (id remap, re-authored)
            v = stats[f][k]; v[0] += 1
            for i in range(5):
                if c >> i & 1: v[i + 1] += 1
            samples.append((f, x, o, k, c))
    tot = collections.defaultdict(lambda: [0] * 6)
    for s in stats:
        for k, v in s.items():
            t = tot[k]
            for i in range(6): t[i] += v[i]
    rules = make_rules(tot)
    folds = [make_rules(stats[0]), make_rules(stats[1])]
    pickle.dump(dict(rules=rules, folds=folds, ids=learn_ids()[0]), open(RULES, 'wb'))
    print('base informative words', len(samples), 'keys', len(tot), 'ruled keys', len(rules))
    return rules, folds, samples

# ---------------------------------------------------------------------------------------------- id remap detector (IDR)
ID_T = (2, 6, 7, 8, 11)
def id_forms(xw, pw, base):
    """id classes consistent with Xbox word -> PC word under the base id maps: {('32',T) | ('16a',T) | ('16b',T)}, plus
    whether a real remap (mapped value != source) was seen"""
    v = struct.unpack('>I', xw)[0]; pv = struct.unpack('<I', pw)[0]
    a, b = struct.unpack('>HH', xw); pa, pb = struct.unpack('<HH', pw)
    out = set(); remap = False
    for t in ID_T:
        m = base.get(t)
        if not m: continue
        if v in m and m[v] == pv: out.add(('32', t)); remap |= m[v] != v
        if a in m and m[a] == pa and b == pb and a not in (0, 0xffff): out.add(('16a', t)); remap |= m[a] != a
        if b in m and m[b] == pb and a == pa and b not in (0, 0xffff): out.add(('16b', t)); remap |= m[b] != b
    return out, remap

def learn_ids():
    """key -> (form, T) where every informative base sample of the key is that id (n >= MIN_N, >= 5 real remaps)"""
    import dtpid_sweep as DS
    _, ids = DS.ctx(); base = ids.base
    st = [collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter()]) for _ in range(2)]
    samples = []
    for x, p, xb, pc, xr in base_pairs():
        f = fold(xb['src']); xd, pd = xb['data'], pc['data']
        for o, k in word_keys(xd, xr):
            xw, pw = xd[o:o + 4], pd[o:o + 4]
            if xw == pw == xw[::-1]: continue
            forms, remap = id_forms(xw, pw, base)
            v = st[f][k]; v[0] += 1
            for fm in forms: v[1][fm] += 1
            if remap:
                for fm in forms: v[2][fm] += 1
            samples.append((f, x, o, k, frozenset(forms)))
    def mk(stat_list):
        r = {}
        tot = collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter()])
        for stt in stat_list:
            for k, v in stt.items():
                t = tot[k]; t[0] += v[0]; t[1].update(v[1]); t[2].update(v[2])
        for k, (n, c, rm) in tot.items():
            if n < MIN_N or not c: continue
            fm, cnt = c.most_common(1)[0]
            if cnt == n and rm[fm] >= 5: r[k] = fm
        return r
    return mk(st), [mk([st[0]]), mk([st[1]])], samples

def id_findings(xd, rel, pd, idr, ids):
    out = []
    for o, k in word_keys(xd, rel):
        fm = idr.get(k)
        if fm is None: continue
        form, t = fm; xw, pw = xd[o:o + 4], pd[o:o + 4]
        if form == '32':
            v = struct.unpack('>I', xw)[0]
            if v in (0, 0xffffffff): continue
            want = struct.pack('<I', ids(t, v) & 0xffffffff)
        else:
            a, b = struct.unpack('>HH', xw)
            if form == '16a':
                if a in (0, 0xffff): continue
                want = struct.pack('<HH', ids(t, a) & 0xffff, b)
            else:
                if b in (0, 0xffff): continue
                want = struct.pack('<HH', a, ids(t, b) & 0xffff)
        if pw != want:
            out.append(('IDR', o, xw.hex(), pw.hex(), want.hex(), 'id%s:%d' % (form, t)))
    return out

_IDR = None
def id_rules():
    global _IDR
    if _IDR is None:
        d = pickle.load(open(RULES, 'rb')) if os.path.exists(RULES) else {}
        if 'ids' not in d:
            d['ids'] = learn_ids()[0]
            if d: pickle.dump(d, open(RULES, 'wb'))
        _IDR = d['ids']
    return _IDR

_RULES = None
def rules():
    global _RULES
    if _RULES is None:
        _RULES = pickle.load(open(RULES, 'rb'))['rules'] if os.path.exists(RULES) else learn()[0]
    return _RULES

def fp_findings(xd, rel, pd, rl):
    out = []
    for o, k in word_keys(xd, rel):
        r = rl.get(k)
        if r is None: continue
        xw, pw = xd[o:o + 4], pd[o:o + 4]
        c = cls(xw, pw)
        if c == 0 or c >> r & 1: continue
        want = bytes(xw[j] for j in PERMS[NAMES[r]])
        xv = struct.unpack('>I', xw)[0]; pv = struct.unpack('<I', pw)[0]; wv = struct.unpack('<I', want)[0]
        kind = 'MAG' if (1 <= xv <= 0xffff and pv >= 0x10000 and wv < 0x10000) else 'FP'
        got = [NAMES[i] for i in range(5) if c >> i & 1]
        out.append((kind, o, xw.hex(), pw.hex(), want.hex(), '/'.join(got), NAMES[r]))
    return out

# ------------------------------------------------------------------------------------------------------------ overlay
def overlay(dirs, names=None):
    files = {}
    for d in dirs:
        d = d if os.path.isabs(d) else os.path.join(W, d)
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.lower().endswith('.drm'):
                    files[os.path.relpath(os.path.join(r, f), d).replace('\\', '/')] = os.path.join(r, f)
    if names: files = {k: v for k, v in files.items() if k in names or os.path.basename(k) in names}
    return files

_XS = {}
def xsecs(rel):
    if rel not in _XS:
        from soundplex_fix import xsecs_of
        try: _XS[rel] = xsecs_of(rel)
        except Exception: _XS[rel] = None
    return _XS[rel]

def section_pairs(xs, D):
    """[(xbox sec dict, pc section index)] - by index when the DRM layout matches, else type 7 by remapped id"""
    if len(xs) == len(D.sections) and all(x['type'] == p.type for x, p in zip(xs, D.sections)):
        return [(x, i) for i, x in enumerate(xs) if x['data'] is not None]
    import dtpid_sweep as DS
    _, ids = DS.ctx(); ids.local = {}
    return list(DS.pairs(xs, D, ids))

def base_content(x):
    """True when the Xbox section is byte-identical to a base Xbox section (pc_copy/template route: PC bytes)"""
    import dtpid_sweep as DS
    st, _ = DS.ctx()
    b = st['xb_store'].get((x['type'], x['id']))
    return b is not None and b['data'] == x['data'] and b['reloc'] == x['reloc']

def audit_file(rel, path, rl, do_fp=True):
    xs = xsecs(rel)
    if xs is None: return None, []
    raw = open(path, 'rb').read(); D = DW.read(raw, 'le')
    finds = []
    for x, i in section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] not in (0, 7, 8) or len(sec.data) != len(x['data']): continue
        xr = R.parse(x['reloc'], 'be')
        _, slog = fix_strings(x['data'], xr, sec.data, x['type'], kinds=('STR', 'STR8', 'NODE0'), preloc=sec.reloc)
        for kind, a, old, new in slog:
            finds.append(dict(file=rel, type=x['type'], id=sec.id, xid=x['id'], det=kind, off=a, pc=old.hex(), want=new.hex(),
                              text=new.rstrip(b'\0').decode('ascii', 'replace') if kind != 'NODE0' else 'u32 %d' % new[0]))
        if do_fp and x['type'] == 7 and not base_content(x):
            import dtpid_sweep as DS
            _, ids = DS.ctx()
            for kind, o, xw, pw, want, rule in id_findings(x['data'], xr, sec.data, id_rules(), ids):
                finds.append(dict(file=rel, type=7, id=sec.id, xid=x['id'], det=kind, off=o, xbox=xw, pc=pw, want=want, got='', rule=rule))
            for kind, o, xw, pw, want, got, rule in fp_findings(x['data'], xr, sec.data, rl):
                finds.append(dict(file=rel, type=7, id=sec.id, xid=x['id'], det=kind, off=o, xbox=xw, pc=pw, want=want, got=got, rule=rule))
    return D, finds

def resolve_set(s):
    if s in (None, 'installed'): return INSTALLED
    return s.split(',')

# ---------------------------------------------------------------------------------------------------------- commands
def cmd_validate():
    import dtpid_sweep as DS
    st, ids = DS.ctx()
    n = {'STR': 0, 'STR8': 0}; bad = collections.Counter(); changed = 0
    for t in (0, 7, 8):
        for (tt, x), xb in st['xb_store'].items():
            if tt != t: continue
            p = ids.base.get(t, {}).get(x); pc = st['pc_store'].get((t, p)) if p is not None else None
            if pc is None or len(pc['data']) != len(xb['data']): continue
            xr = R.parse(xb['reloc'], 'be')
            for a, z, kind in string_spans(xb['data'], xr): n[kind] += 1
            if t == 7 and node0(xb['data'], xr): n['NODE0'] = n.get('NODE0', 0) + 1
            nb, log = fix_strings(xb['data'], xr, pc['data'], t, kinds=('STR', 'STR8', 'NODE0'))
            for l in log: bad[l[0]] += 1
            if nb != pc['data']: changed += 1
    print('STRINGS on base pairs (types 0/7/8): spans', n, 'spans where real PC != Xbox', dict(bad), 'sections the fix would change', changed)
    rl, folds, samples = learn()
    cov = fp = mag = 0; tot = len(samples); ex = collections.Counter()
    for f, x, o, k, c in samples:
        r = folds[1 - f].get(k)
        if r is None: continue
        cov += 1
        if not c >> r & 1: fp += 1; ex[x] += 1
    print('FP rule held-out 2-fold by DRM on real PC bytes: informative words %d, covered %.3f, flagged %d (rate %.1e), '
          'in %d DTPs; top %s' % (tot, cov / tot, fp, fp / max(cov, 1), len(ex), ex.most_common(5)))
    idr, ifolds, isamp = learn_ids()
    icov = ifp = 0; iex = collections.Counter()
    for f, x, o, k, forms in isamp:
        fm = ifolds[1 - f].get(k)
        if fm is None: continue
        icov += 1
        if fm not in forms: ifp += 1; iex[x] += 1
    print('IDR rule (id remap expected) held-out 2-fold: ruled keys %d, covered words %d, flagged %d (rate %.1e) top %s' % (
        len(idr), icov, ifp, ifp / max(icov, 1), iex.most_common(5)))
    fp_in = sum(1 for f, x, o, k, c in samples if k in rl and not c >> rl[k] & 1)
    print('FP rule in-sample (all base rules on base PC bytes): flagged', fp_in, '(0 by construction: rules need 100% agreement)')

def cmd_scan(dirs, out_json=None, verbose=False, names=None):
    rl = rules(); allf = []; perfile = collections.Counter()
    for rel, path in sorted(overlay(dirs, names).items()):
        _, f = audit_file(rel, path, rl)
        for x in f: x['src'] = os.path.relpath(path, W)
        allf += f
        for x in f: perfile[rel, x['det']] += 1
    by = collections.Counter(x['det'] for x in allf)
    print('findings', dict(by), 'files', len({r for r, _ in perfile}))
    for x in allf:
        if x['det'] in ('STR', 'STR8', 'NODE0'):
            print('  %-4s %-40s t%d id %5d @%#06x pc %s -> %r' % (x['det'], x['file'], x['type'], x['id'], x['off'], x['pc'], x['text']))
    for x in allf:
        if x['det'] in ('MAG', 'IDR') or (verbose and x['det'] == 'FP'):
            print('  %-4s %-40s DTP %5d @%#06x xbox %s pc %s (%s) rule %s -> %s' % (x['det'], x['file'], x['id'], x['off'], x['xbox'],
                                                                              x['pc'], x['got'], x['rule'], x['want']))
    fpf = collections.Counter((x['file'], x['id']) for x in allf if x['det'] in ('FP', 'MAG'))
    print('FP/MAG by DTP (top 40):')
    for (f, i), c in fpf.most_common(40): print('   %4d  %s DTP %d' % (c, f, i))
    if out_json:
        json.dump(allf, open(out_json, 'w'), indent=0)
        print('wrote', out_json)
    return allf

CONTROLS = [  # (label, overlay dir (pre-fix version), file, DTP id, offset, detector expected)
    ('raft chain_free (fix19)', 'mods_glitchfix', 'dlc1_uo_raft_bridge.drm', 20765, 0x520, ('STR',)),
    ('sewer_gate SoundPlex group raw (fix16)', 'mods_next', 'dlc1_uo_sewer_gate.drm', 21104, 0x450, ('MAG', 'FP')),
    ('caverns_hall SoundPlex COUNT raw (fix18 OOM)', 'mods_current', 'dlc_caverns_hall.drm', 23469, 0x1e4, ('MAG', 'FP')),
    ('chunkdoll {u8,u8,u16} hdr (fix18)', 'vm_mods_expected', 'knight_thrall_chunkdoll.drm', 20951, 0x130, ('FP', 'MAG')),
    ('chunkdoll {u8,u8,u16} hdr (fix18)', 'vm_mods_expected', 'knight_thrall_chunkdoll.drm', 20951, 0x158, ('FP', 'MAG')),
    ('adren_trap event list hdr (fix14)', 'vm_mods_expected', 'dlc1_uo_adren_trap.drm', 20940, None, ('FP', 'MAG')),
    ('caverns aidata count (fix15)', 'mods_glitchfix', 'dlc_caverns.drm', 20872, None, ('FP', 'MAG')),
]
def cmd_controls():
    rl = rules()
    for label, d, f, sid, off, dets in CONTROLS:
        path = os.path.join(W, d, f)
        if not os.path.exists(path): print('  ?? missing', path); continue
        _, fs = audit_file(f, path, rl)
        hit = [x for x in fs if x['id'] == sid and x['det'] in dets and (off is None or x['off'] == off)]
        oth = sum(1 for x in fs if x['id'] == sid)
        print('  %-5s %-45s %s DTP %d %s: %d hit(s) (findings in this DTP: %d) %s' % (
            'FOUND' if hit else 'MISS', label, f, sid, hex(off) if off is not None else '*', len(hit), oth,
            [(x['det'], hex(x['off']), x.get('xbox'), x['pc'], x['want']) for x in hit[:3]]))

def cmd_fix(out, dirs, names):
    os.makedirs(out, exist_ok=True); md5 = []
    for rel, path in sorted(overlay(dirs, names or None).items()):
        xs = xsecs(rel)
        if xs is None: continue
        raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logs = []
        for x, i in section_pairs(xs, D):
            sec = D.sections[i]
            nb, log = fix_strings(x['data'], x['reloc'], sec.data, x['type'], preloc=sec.reloc)
            if log: sec.data = nb; logs += [(x['type'], sec.id) + l for l in log]
        if not logs: continue
        o = D.write('le')
        if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(o)
        # idempotence: re-run on the output changes nothing
        D2 = DW.read(o, 'le'); again = sum(len(fix_strings(x['data'], x['reloc'], D2.sections[i].data, x['type'], preloc=D2.sections[i].reloc)[1])
                                           for x, i in section_pairs(xs, D2))
        # only the logged byte ranges changed: every other section byte-identical, headers/relocs identical
        D0 = DW.read(raw, 'le'); diff = []
        for k, (a0, a2) in enumerate(zip(D0.sections, D2.sections)):
            assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
            if a0.data != a2.data: diff += [(k, j) for j in range(len(a0.data)) if a0.data[j] != a2.data[j]]
        assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
        h = hashlib.md5(o).hexdigest(); md5.append('%s  %s' % (h, rel))
        print(rel, '<-', os.path.relpath(path, W), 'recheck', again, 'bytes changed', len(diff), h)
        for t, sid, kind, a, old, new in logs: print('   type %d id %d %s @%#x %r -> %r' % (t, sid, kind, a, old, new))
    return md5

if __name__ == '__main__':
    a = sys.argv[1:]
    def opt(name, default=None):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return default
    verbose = '-v' in a
    if verbose: a.remove('-v')
    st = opt('--set'); js = opt('--json')
    cmd = a[0]
    if cmd == 'learn': learn()
    elif cmd == 'validate': cmd_validate()
    elif cmd == 'scan': cmd_scan(resolve_set(st), js, verbose, set(a[1:]) or None)
    elif cmd == 'controls': cmd_controls()
    elif cmd == 'fix':
        out = a[1] if os.path.isabs(a[1]) else os.path.join(W, a[1])
        md5 = cmd_fix(out, resolve_set(st), set(a[2:]))
        open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n'); print('wrote', os.path.join(out, 'md5.txt'))
