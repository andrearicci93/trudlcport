"""SoundPlex node DATA words, all node types (generalises soundplex_fix.py, which only knows type 4).

Background (fix18 OOM, dump work/crash/fix18_oom_dialog.dmp, NOTES 2026-10-11): walker 0x5920b0 case 5 (0x59230b) builds
0x590ce0(data): data = {+0 ptr child node, +4 u32 COUNT, +8 ptr, +0xc ptr}; 0x590dad reads COUNT and allocates 16*COUNT
(0x590db9 mul, 0x574940 -> heap 0x597430).  dlc_caverns_hall DTP 23469 +0x1e4: Xbox 00000001 left raw (LE 0x01000000)
-> request 0x10000000 = 256 MB -> 'Out of memory requesting 268435456 bytes' (fatal, TR8-Menu-Hook dialog + exit).

Node = {u32 type 0..13 (BE), ptr data} : internal reloc at o, BE word at o-4 in 0..13, o-4 not a reloc slot.
calibrate: over base Xbox/PC DTP pairs (same size + same internal relocs) collect, per (type, k) for k in 4..WIN step 4,
the byte class of non-pointer data words (PC bytes as a permutation of Xbox bytes).  A (type, k) is RULED when n >= MIN_N
and one class covers >= PURITY of the informative samples (words whose permutations are distinguishable).
scan/patch: for DLC DTPs (Xbox source via soundplex_fix.xsecs_of, paired by remapped id), every ruled non-pointer word of
a node record whose converted bytes != class(Xbox bytes) is reported / rewritten.
CLI: tools/venv/bin/python -I tools/soundplex_nodes.py calibrate
     tools/venv/bin/python -I tools/soundplex_nodes.py scan DIR[,DIR..] [name.drm ..]
     tools/venv/bin/python -I tools/soundplex_nodes.py patch OUTDIR DIR[,DIR..] name.drm ..
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW, dtpid_sweep as DS
from soundplex_fix import load_overlay, xsecs_of

def _is_node(xd, it, a):
    return a is not None and a % 4 == 0 and a + 8 <= len(xd) and struct.unpack_from('>I', xd, a)[0] <= 13 and (a + 4) in it
# type 5 (0x590ce0): {+0 ptr child node, +4 u32 count, +8 ptr, +0xc ptr}
STRICT = {5: lambda xd, it, tg: _is_node(xd, it, it.get(tg)) and (tg + 8) in it and (tg + 0xc) in it}
WIN = 0x48; MIN_N = 20; PURITY = 0.995
PERMS = {'u32': (3, 2, 1, 0), 'u16u16': (1, 0, 3, 2), 'u8u8u16': (0, 1, 3, 2), 'u16u8u8': (1, 0, 2, 3), 'raw': (0, 1, 2, 3)}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'soundplex_nodes_rules.pkl')

def nodes(xd, xreloc):
    rel = R.parse(xreloc, 'be'); it = dict(rel.internal); slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    out = []
    for o, tg in rel.internal:
        if o < 4 or o % 4 or (o - 4) in slots: continue
        t = struct.unpack_from('>I', xd, o - 4)[0]
        if t > 13 or tg % 4 or tg >= len(xd): continue
        if STRICT.get(t) and not STRICT[t](xd, it, tg): continue
        out.append((t, tg))
    return out, slots

def classes(xw, pw):
    return frozenset(n for n, pm in PERMS.items() if bytes(xw[i] for i in pm) == pw)

def calibrate():
    st, ids = DS.ctx()
    stat = collections.defaultdict(collections.Counter)
    for (t, x), xb in st['xb_store'].items():
        if t != 7: continue
        p = ids.base[7].get(x); pc = st['pc_store'].get((7, p)) if p is not None else None
        if pc is None or len(pc['data']) != len(xb['data']): continue
        if dict(R.parse(pc['reloc'], 'le').internal) != dict(R.parse(xb['reloc'], 'be').internal): continue
        nd, slots = nodes(xb['data'], xb['reloc'])
        for typ, tg in nd:
            for k in range(4, WIN, 4):
                q = tg + k
                if q + 4 > len(xb['data']) or q in slots: continue
                c = classes(xb['data'][q:q + 4], pc['data'][q:q + 4])
                if len(c) == len(PERMS): continue                 # all-equal bytes: uninformative
                stat[typ, k][c if c else 'none'] += 1
    rules = {}
    for key, cnt in sorted(stat.items()):
        n = sum(cnt.values())
        best = None
        for name in PERMS:
            cov = sum(v for c, v in cnt.items() if c != 'none' and name in c)
            if best is None or cov > best[1]: best = (name, cov)
        if n >= MIN_N and best[1] >= PURITY * n: rules[key] = best[0]
        if key[0] == 5 or key in rules and key[1] <= 8:
            print('type %2d +0x%02x n=%5d best=%s %.4f %s' % (key[0], key[1], n, best[0], best[1] / n, 'RULE' if key in rules else ''))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    pickle.dump(rules, open(CACHE, 'wb'))
    print('rules', len(rules), 'by type', collections.Counter(k[0] for k in rules))
    return rules

def load_rules():
    return pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else calibrate()

# only fields proven against the engine (0x590ce0) are applied; other learned (type, k) are reported by calibrate only
APPLY = {(5, 4)}

def fix_section(xd, xreloc, pd, rules):
    rules = {k: v for k, v in rules.items() if k in APPLY}
    b = bytearray(pd); log = []
    nd, slots = nodes(xd, xreloc)
    for typ, tg in nd:
        for k in range(4, WIN, 4):
            r = rules.get((typ, k)); q = tg + k
            if r is None or q + 4 > len(xd) or q in slots: continue
            w = bytes(xd[q + i] for i in PERMS[r])
            if b[q:q + 4] != w:
                log.append((typ, tg, k, r, bytes(b[q:q + 4]).hex(), w.hex())); b[q:q + 4] = w
    return bytes(b), log

def process(rel, path, rules, ids):
    xs = xsecs_of(rel)
    if xs is None: return None, []
    raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logs = []
    for s, i in DS.pairs(xs, D, ids):
        sec = D.sections[i]
        if len(sec.data) != len(s['data']): continue
        new, log = fix_section(s['data'], s['reloc'], sec.data, rules)
        if log: sec.data = new; logs += [(sec.id,) + l for l in log]
    if not logs: return None, []
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    return out, logs

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'calibrate': calibrate(); sys.exit()
    rules = load_rules(); st, ids = DS.ctx(); ids.local = {}
    if cmd == 'selftest':                                   # rules applied to the REAL PC bytes of base pairs: words changed
        n = c = 0
        for (t, x), xb in st['xb_store'].items():
            if t != 7: continue
            p = ids.base[7].get(x); pc = st['pc_store'].get((7, p)) if p is not None else None
            if pc is None or len(pc['data']) != len(xb['data']): continue
            if dict(R.parse(pc['reloc'], 'le').internal) != dict(R.parse(xb['reloc'], 'be').internal): continue
            _, log = fix_section(xb['data'], xb['reloc'], pc['data'], rules); n += 1; c += len(log)
            if log and c <= 30: print('  base', x, '->', p, log[:3])
        print('base pairs', n, 'words the rules would change on real PC bytes', c)
    elif cmd == 'scan':
        tot = collections.Counter()
        for rel, path in sorted(load_overlay(sys.argv[2].split(','), set(sys.argv[3:]) or None).items()):
            _, logs = process(rel, path, rules, ids)
            if logs:
                tot[rel] = len(logs)
                print(rel, len(logs), [(l[0], l[1], hex(l[2]), hex(l[3]), l[4], l[5], l[6]) for l in logs[:8]])
        print('TOTAL words', sum(tot.values()), 'files', len(tot))
    elif cmd == 'patch':
        out = sys.argv[2]
        for rel, path in sorted(load_overlay(sys.argv[3].split(','), set(sys.argv[4:])).items()):
            new, logs = process(rel, path, rules, ids)
            for l in logs: print(rel, 'DTP', l[0], 'node type', l[1], 'data', hex(l[2]), '+%#x' % l[3], l[4], l[5], '->', l[6])
            if new is not None:
                dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst) or out, exist_ok=True)
                open(dst, 'wb').write(new); print('wrote', dst)
