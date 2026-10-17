"""model_point_fix.py - typed Xbox(BE)->PC(LE) fix for the per-model 'point' arrays of model DTPs (Xbox word0 0x04c20453) that the
learned type-7 table converts with the wrong byte permutation (case found: raft-bridge chain not targetable in DLC1 watertunnel).

Structures (model header: {u32 nseg @4, ptr seg[] @0xc} ... {u32 n @0x5c, ptr @0x60}; segments 0x40 B, HInfo* @+0x3c):
  TP  target/markup points (header +0x5c/+0x60), 32 B: {u16 seg, u16 TYPE} {f32 x,y,z} {f32 rx,ry,rz} {u32 ID}
      Engine (PC exe, unpacked, VA): 0x716860 walks model->points: movzx eax, word [pt+2] = TYPE; TYPE&1 -> flags 0x71 (combat target,
      enemies), &4 -> 2 (grapple), &8 -> 4, &0x40 -> 8; registers (instance, flags, [pt+0x1c] ID) in 7 target lists via 0x7164d0.
      ID is a lookup key (0x4d4e13, 0x6b96ca compare [pt+0x1c] with the message datum [0xd98f9c]+0x10).
      Base Xbox/PC: word +0 is ALWAYS a u16 pair (s16); the ID numbering differs per platform (enum) but is only matched inside the model.
  HS/HB/HC  HInfo hit spheres (36 B), boxes (68 B), capsules (56 B): {u16 flags, u8 id, u8 rank, ...} etc.
Rules: per (kind, word offset) the byte permutation that ALL informative base pairs agree on (>= MIN_N informative samples), learned on
the 1055 base model DTP pairs (same size, same internal relocs); arrays are used only when the element size is provable
(next reloc target - array == n * size).  A word is rewritten only if every permutation still consistent with the rule gives the same
bytes (ambiguity -> left alone).  Pointer / id-reloc slots are never touched.
Usage:
  tools/venv/bin/python -I tools/model_point_fix.py learn            -> work/chain_aim/model_point_rules.pkl (+ 2-fold held-out report)
  tools/venv/bin/python -I tools/model_point_fix.py selftest         (apply on REAL PC bytes of all base pairs: must change 0 words)
  tools/venv/bin/python -I tools/model_point_fix.py scan [--set installed|DIR,DIR..]
  tools/venv/bin/python -I tools/model_point_fix.py fix OUTDIR [--set ..] [names..]   (writes changed DRMs + md5.txt, only logged bytes change)
Pipeline hook (not wired): fix_section(xd, xreloc_be, pd) -> (bytes, log) for type-7 sections, after model_fix.
"""
import sys, os, struct, collections, pickle, zlib, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
RULES = os.path.join(W, 'chain_aim', 'model_point_rules.pkl')
MAGIC = bytes.fromhex('04c20453')
PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
NAMES = list(PERMS)
MIN_N = 20
HSIZE = {0: ('HS', 36), 1: ('HB', 68), 3: ('HC', 56)}       # HInfo array index -> (kind, element size); 2 = markers (model_fix-safe s32)
TP_SIZE = 32

def perm(w, p): return bytes(w[j] for j in PERMS[p])
def cls(xw, pw): return frozenset(n for n in NAMES if perm(xw, n) == pw)

def elements(xd, rel):
    """yield (kind, element offset, element size) for every provable TP / HInfo element of a model DTP (Xbox data)"""
    if xd[:4] != MAGIC or len(xd) < 0x80: return
    it = dict(rel.internal)
    tg = sorted(set(it.values()) | {len(xd)})
    def nxt(a): return min([v for v in tg if v > a], default=len(xd))
    n = struct.unpack_from('>I', xd, 0x5c)[0]; a = it.get(0x60)
    if n and a is not None and nxt(a) - a == TP_SIZE * n and a + TP_SIZE * n <= len(xd):
        for q in range(n): yield 'TP', a + TP_SIZE * q, TP_SIZE
    seg = it.get(0xc); ns = struct.unpack_from('>I', xd, 4)[0]
    if seg is None or seg + 0x40 * ns > len(xd): return
    for j in range(ns):
        h = it.get(seg + 0x40 * j + 0x3c)
        if h is None or h + 0x28 > len(xd): continue
        for k, (kind, es) in HSIZE.items():
            c = struct.unpack_from('>I', xd, h + 8 * k)[0]; a = it.get(h + 8 * k + 4)
            if not c or a is None or nxt(a) - a != es * c: continue
            for q in range(c): yield kind, a + es * q, es

def base_pairs():
    import generic_store, dlc_generic as DG
    st = generic_store.load(); ids = DG.DlcIds(st, None)
    out = []
    for (t, x), xb in st['xb_store'].items():
        if t != 7 or xb['data'][:4] != MAGIC: continue
        pc = st['pc_store'].get((7, ids.base[7].get(x)))
        if pc is None or len(pc['data']) != len(xb['data']): continue
        rel = R.parse(xb['reloc'], 'be')
        if dict(R.parse(pc['reloc'], 'le').internal) != dict(rel.internal): continue
        out.append((x, xb['src'], xb['data'], rel, pc['data']))
    return out

def stats(pairs):
    stat = collections.defaultdict(collections.Counter)
    for x, src, xd, rel, pd in pairs:
        slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
        for kind, e, es in elements(xd, rel):
            for off in range(0, es, 4):
                o = e + off
                if o in slots or o + 4 > len(xd): continue
                stat[kind, off][cls(xd[o:o + 4], pd[o:o + 4])] += 1
    return stat

SKIP = {('TP', 0x1c)}     # target ID: platform-specific enum (Xbox->PC renumbered in 32/79 base pairs); kept as the Xbox value
                          # (matched only inside the same model, see 0x4d4e13/0x6b96ca); byte order handled by the table (s32)
def make_rules(stat, n_min=MIN_N):
    rules = {}
    for key, c in stat.items():
        if key in SKIP: continue
        cand = set(NAMES); inf = 0; bad = 0
        for cl, m in c.items():
            if len(cl) == len(NAMES): continue
            if not cl: bad += m; continue
            cand &= cl; inf += m
        if inf >= n_min and cand and not bad: rules[key] = (tuple(sorted(cand)), inf, bad)
    return rules

def fold(src): return zlib.crc32(src.encode()) & 1

def learn():
    pairs = base_pairs()
    stat = stats(pairs); rules = make_rules(stat)
    print('base model pairs', len(pairs), 'ruled (kind,offset)', len(rules))
    for key in sorted(rules): print('  %s +0x%02x %-12s informative %4d remap/none %d' % (key[0], key[1], '/'.join(rules[key][0]), rules[key][1], rules[key][2]))
    # 2-fold held-out by DRM: rules from one fold applied on the REAL PC bytes of the other fold must change nothing
    ho = collections.Counter()
    for f in (0, 1):
        tr = [p for p in pairs if fold(p[1]) != f]; te = [p for p in pairs if fold(p[1]) == f]
        r = make_rules(stats(tr))
        for x, src, xd, rel, pd in te:
            nb, log = fix_section(xd, rel, pd, r)
            ho['pairs'] += 1; ho['words_changed'] += len(log); ho['pairs_changed'] += bool(log)
            for l in log[:3]: print('   HELD-OUT CHANGE', src, x, l)
    print('2-fold held-out:', dict(ho))
    pickle.dump(dict(rules=rules, stat={k: dict(v) for k, v in stat.items()}), open(RULES, 'wb'))

_RL = None
def rules():
    global _RL
    if _RL is None: _RL = pickle.load(open(RULES, 'rb'))['rules']
    return _RL

def fix_section(xd, xrel, pd, rl=None):
    """xd: Xbox data, xrel: parsed BE reloc (or raw blob), pd: PC bytes (same size). -> (new PC bytes, log[(kind, off, elem, old, new, perm)])"""
    if isinstance(xrel, (bytes, bytearray)): xrel = R.parse(xrel, 'be')
    if xd[:4] != MAGIC or len(pd) != len(xd): return pd, []
    rl = rules() if rl is None else rl
    out = bytearray(pd); log = []
    slots = set(xrel.pointer_offsets()) | set(xrel.id_offsets())
    for kind, e, es in elements(xd, xrel):
        for off in range(0, es, 4):
            r = rl.get((kind, off)); o = e + off
            if r is None or o in slots or o + 4 > len(xd): continue
            xw = xd[o:o + 4]; outs = {perm(xw, p) for p in r[0]}
            if len(outs) != 1: continue                          # ambiguous rule for this value
            want = outs.pop()
            if bytes(out[o:o + 4]) != want:
                log.append((kind, o, e, bytes(out[o:o + 4]).hex(), want.hex(), '/'.join(r[0])))
                out[o:o + 4] = want
    return bytes(out), log

def selftest():
    pairs = base_pairs(); c = collections.Counter()
    for x, src, xd, rel, pd in pairs:
        nb, log = fix_section(xd, rel, pd)
        c['pairs'] += 1; c['words_changed'] += len(log); c['pairs_changed'] += bool(log)
        for l in log[:3]: print('  CHANGE', src, x, l)
    print('selftest on real PC bytes of base pairs:', dict(c))
    return c['words_changed'] == 0

# ------------------------------------------------------------------------------------------------- DLC files (installed overlay)
def _dlc_files(dirs, names=None):
    import dtp_audit as DA
    return DA.overlay(dirs, names)

def file_fixes(rel, path):
    import dtp_audit as DA, drm_write as DW
    xs = DA.xsecs(rel)
    if xs is None: return None, None, []
    raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logs = []
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or x['data'][:4] != MAGIC or len(sec.data) != len(x['data']): continue
        nb, log = fix_section(x['data'], R.parse(x['reloc'], 'be'), sec.data)
        if log: sec.data = nb; logs += [(sec.id, x['id']) + l for l in log]
    return raw, D, logs

def cmd_scan(dirs, names=None):
    tot = 0
    for rel, path in sorted(_dlc_files(dirs, names).items()):
        raw, D, logs = file_fixes(rel, path)
        if raw is None: print('  (no Xbox source resolved)', rel); continue
        for l in logs: print('%s [%s] DTP %d (xbox %d) %s @0x%x (elem 0x%x) pc %s -> %s (%s)' % ((rel, os.path.relpath(path, W)) + l))
        tot += len(logs)
    print('TOTAL words', tot)

def cmd_fix(out, dirs, names=None):
    import drm_write as DW
    os.makedirs(out, exist_ok=True); md5 = []
    for rel, path in sorted(_dlc_files(dirs, names).items()):
        raw, D, logs = file_fixes(rel, path)
        if not logs: continue
        o = D.write('le')
        if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(o)
        # checks: idempotent, only logged words changed, headers / relocs / names identical
        _, D2, again = file_fixes(rel, dst)
        D0 = DW.read(raw, 'le'); changed = set()
        assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
        for k, (a0, a2) in enumerate(zip(D0.sections, D2.sections)):
            assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
            if a0.data != a2.data:
                changed |= {(a0.id, j - j % 4) for j in range(len(a0.data)) if a0.data[j] != a2.data[j]}
        logged = {(l[0], l[3]) for l in logs}
        assert changed <= logged, (changed - logged)
        h = hashlib.md5(o).hexdigest(); md5.append('%s  %s' % (h, rel))
        print(rel, '<-', os.path.relpath(path, W), 'recheck', len(again), 'words changed', len(changed), 'md5', h)
        for l in logs: print('   DTP %d (xbox %d) %s @0x%x (elem 0x%x) %s -> %s (%s)' % l)
    open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
    return md5

if __name__ == '__main__':
    a = sys.argv[1:]
    st = None
    if '--set' in a:
        i = a.index('--set'); st = a[i + 1]; del a[i:i + 2]
    import dtp_audit as DA
    dirs = DA.INSTALLED + ['mods_fix20'] if st in (None, 'installed') else st.split(',')
    if a[0] == 'learn': learn()
    elif a[0] == 'selftest': sys.exit(0 if selftest() else 1)
    elif a[0] == 'scan': cmd_scan(dirs, set(a[1:]) or None)
    elif a[0] == 'fix': cmd_fix(a[1] if os.path.isabs(a[1]) else os.path.join(W, a[1]), dirs, set(a[2:]) or None)
