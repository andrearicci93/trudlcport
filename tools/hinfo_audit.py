"""hinfo_audit.py - collision/hit-prim (HInfo) audit of model DTPs (Xbox word0 0x04c20453), Xbox(BE)->PC(LE).
HInfo (per segment, seg+0x3c): {u32 n, ptr} x5 = spheres, boxes, markers, capsules, geoms(?).
Element layouts (cdcEditor tr8_model.py): sphere 36B {u16 flags, u8 id, u8 rank, u8 pad, .., u16 radius@6, s16 xyz@8, u32 r2@0x10,
u16 mass@0x14, u8 buoy@0x16, u8 expl@0x18, s32 material@0x1a?, s16 damage@0x1e}; box 72B {vec4 dim, vec4 pos, quat, u16 flags@0x30,
u8 id, u8 rank, ..}; marker 32B; capsule 60B {vec4 pos, quat, u16 flags@0x20, u8 id, u8 rank, ..}.
learn : per (array k, word offset in element) the byte-permutation classes on all base pairs -> work/chain_aim/hinfo_rules.pkl
check FILE.. : compare converted DLC model DTPs against the rules (source = Xbox DLC DRM of the same name)
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
MAGIC = bytes.fromhex('04c20453')
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
RULES = os.path.join(W, 'chain_aim', 'hinfo_rules.pkl')
PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
NAMES = list(PERMS)
def cls(xw, pw):
    return frozenset(n for n, p in PERMS.items() if bytes(xw[j] for j in p) == pw)

def arrays(xd, rel):
    """yield (seg, k, n, array_off, stride_guess) for each HInfo array of each segment"""
    if xd[:4] != MAGIC: return
    it = dict(rel.internal)
    tg = sorted(set(it.values()) | {len(xd)})
    seg = it.get(0xc); n = struct.unpack_from('>I', xd, 4)[0]
    if seg is None or seg + 0x40 * n > len(xd): return
    for j in range(n):
        h = it.get(seg + 0x40 * j + 0x3c)
        if h is None or h + 0x28 > len(xd): continue
        for k in range(5):
            c = struct.unpack_from('>I', xd, h + 8 * k)[0]; a = it.get(h + 8 * k + 4)
            if not c or a is None: continue
            nx = min([v for v in tg if v > a], default=len(xd))
            yield j, k, c, a, (nx - a) // c if c else 0, h

STRIDE = {0: 36, 1: 68, 2: 32, 3: 56}

def learn():
    import generic_store, dlc_generic as DG
    st = generic_store.load(); ids = DG.DlcIds(st, None)
    stat = collections.defaultdict(collections.Counter); strides = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list); npairs = 0
    for (t, x), xb in st['xb_store'].items():
        if t != 7 or xb['data'][:4] != MAGIC: continue
        pc = st['pc_store'].get((7, ids.base[7].get(x)))
        if pc is None or len(pc['data']) != len(xb['data']): continue
        rel = R.parse(xb['reloc'], 'be')
        if dict(R.parse(pc['reloc'], 'le').internal) != dict(rel.internal): continue
        npairs += 1; xd, pd = xb['data'], pc['data']
        ptr = set(rel.pointer_offsets()) | set(rel.id_offsets())
        for j, k, c, a, sg, h in arrays(xd, rel):
            strides[k][sg] += 1
            es = STRIDE.get(k)
            if es is None or sg != es: continue           # element size provable only when the array fills the gap exactly
            for q in range(c):
                for off in range(0, es, 4):
                    o = a + q * es + off
                    if o + 4 > len(xd) or o in ptr: continue
                    xw, pw = xd[o:o + 4], pd[o:o + 4]
                    cl = cls(xw, pw)
                    stat[k, off][cl] += 1
                    if len(samples[k, off]) < 6 and len(cl) < 3: samples[k, off].append((xw.hex(), pw.hex(), x))
    print('pairs', npairs)
    for k in sorted(strides): print('array', k, 'stride guesses', strides[k].most_common(6))
    rules = {}
    for key in sorted(stat):
        c = stat[key]; inter = None; tot = sum(c.values()); inf = 0
        for cl, m in c.items():
            if len(cl) == 5 or not cl: continue
            inf += m
        # candidate perms consistent with ALL informative samples
        cand = set(NAMES)
        bad = 0
        for cl, m in c.items():
            if len(cl) == 5: continue
            if not cl: bad += m; continue
            cand &= cl
        rules[key] = (sorted(cand), inf, bad, tot)
        print('k%d +0x%02x' % key, 'consistent', sorted(cand), 'informative', inf, 'none', bad, 'total', tot,
              ' top', [('/'.join(sorted(cl)) or 'NONE', m) for cl, m in c.most_common(4)], samples[key][:2])
    pickle.dump(dict(rules=rules, stat=dict(stat)), open(RULES, 'wb'))

def check(paths):
    import drm_write as DW
    from convert_dlc import raw_dlc
    from drm import cdrm_decode, sections_with_data
    rules = pickle.load(open(RULES, 'rb'))['rules']
    out = []
    for f in paths:
        _, xs = sections_with_data(cdrm_decode(raw_dlc(os.path.basename(f))[0], 'be'), 'be')
        D = DW.read(open(f, 'rb').read(), 'le')
        for s, o in zip(xs, D.sections):
            if s['type'] != 7 or s['data'][:4] != MAGIC or len(o.data) != len(s['data']): continue
            rel = R.parse(s['reloc'], 'be'); xd, pd = s['data'], o.data
            ptr = set(rel.pointer_offsets()) | set(rel.id_offsets())
            for j, k, c, a, sg, h in arrays(xd, rel):
                es = STRIDE.get(k)
                print('%s DTP %d(pc %d) seg %d arr %d n %d @0x%x stride_guess %d%s' % (os.path.basename(f), s['id'], o.id, j, k, c, a, sg,
                      '' if sg == es else '  (stride not provable -> skipped)'))
                if es is None or sg != es: continue
                for q in range(c):
                    for off in range(0, es, 4):
                        oo = a + q * es + off
                        if oo + 4 > len(xd) or oo in ptr: continue
                        xw, pw = xd[oo:oo + 4], pd[oo:oo + 4]
                        cl = cls(xw, pw); cand, inf, bad, tot = rules.get((k, off), ([], 0, 0, 0))
                        ok = (len(cl) == 5) or (cl & set(cand)) if cand else None
                        flag = '' if ok else ('  <-- RULE %s' % cand if cand else '  (no rule)')
                        if flag or off in (0, 0x30, 0x20):
                            print('   el %d +0x%02x X %s P %s cls %s%s' % (q, off, xw.hex(), pw.hex(), '/'.join(sorted(cl)) or 'NONE', flag))
                        if flag and cand: out.append((os.path.basename(f), s['id'], o.id, j, k, q, off, xw.hex(), pw.hex(), cand))
    return out

if __name__ == '__main__':
    if sys.argv[1] == 'learn': learn()
    elif sys.argv[1] == 'check':
        r = check(sys.argv[2:]); print('VIOLATIONS', len(r))
        for x in r: print(' ', x)
