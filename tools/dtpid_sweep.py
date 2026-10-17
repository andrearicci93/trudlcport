"""DTP-id words WITHOUT reloc in converted DLC DTPs ('dtpid'): sweep + classification + typed patch.

Background (aidata crash 0x54df84, NOTES 2026-10-10): DTP data can hold DTP ids as plain u32 words without an id-ref reloc
(the engine looks them up with 0x54df80 = table[id] without bounds check).  PC stores ids(7, xbox id) there.  The learned
type-7 table converts DLC-new DTPs by (region label, offset) and may give such a word a u32 swap without the id remap or a
u16-pair swap (0x2491 -> 0x24910000 = the crash).
Sweep rule: Xbox BE word == id of a DTP section of the SAME Xbox DRM, that id is remapped on PC (ids(7,x) != x), the word
is not a pointer / id-ref reloc slot.  On base Xbox/PC pairs the PC word is the remapped id in 97% of such words.

Classification per candidate word (installed PC word pv, Xbox word xv, want = ids(7, xv)):
  ok            pv == want (already right)
  pc_same       section is a base DTP and pv == the real PC DTP word at that offset (PC itself) -> FALSE POSITIVE
  analog_id     the PC analog (base DTP of same size + reloc layout, analog_index) stores the REMAPPED id of its own Xbox
                word at that offset -> the slot IS an id slot -> REAL (fix: pv := want)
  analog_noid   the PC analog stores its Xbox word at that offset in another class (raw / u16 pair / not remapped while its
                Xbox word is a remapped id) -> FALSE POSITIVE (the value is something else that equals an id by chance)
  base_rule     no analog: decided by base-pair evidence of the same (record signature) key, see classify()
CLI: tools/venv/bin/python -I tools/dtpid_sweep.py scan DIR[,DIR..] [name.drm ..]       (dirs: later wins)
     tools/venv/bin/python -I tools/dtpid_sweep.py patch OUTDIR DIR[,DIR..] name.drm ..  (fix REAL words only)
     tools/venv/bin/python -I tools/dtpid_sweep.py base                                 (precision of the rule on base pairs)
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
import dlc_generic as DG, generic_store
from drm import cdrm_decode, sections_with_data

def u16p(v):
    b = struct.pack('>I', v)
    return struct.unpack('<I', b[1::-1] + b[:1:-1])[0]

def status(xv, pv, want, ids):
    """class of the installed word: ok (remapped id) | noremap (u32 swap, id not remapped) | u16 (u16-pair swap) |
    byteraw (Xbox bytes copied) | otherid:T (remapped as an id of another type T) | other"""
    if pv == want: return 'ok'
    if pv == xv: return 'noremap'
    if pv == u16p(xv): return 'u16'
    if pv == struct.unpack('<I', struct.pack('>I', xv))[0]: return 'byteraw'
    for t in (2, 5, 6, 8, 10, 11, 12):
        m = ids.base.get(t, {}).get(xv)
        if m is not None and m != xv and m == pv: return 'otherid:%d' % t
    return 'other'

_VE = None
def value_evidence(xv, store=None, ids=None):
    """(n, n remapped) of the SAME-DRM rule on base pairs for Xbox value xv (tools/dtpid_evidence.py,
    work/generic/dtpid_evidence.pkl; overall precision 96.86% = 405577/418707 words)"""
    global _VE
    if _VE is None:
        _VE = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic', 'dtpid_evidence.pkl'), 'rb'))
    return tuple(_VE.get(xv, (0, 0)))

_ST = None; _IDS = None
def ctx():
    global _ST, _IDS
    if _ST is None:
        _ST = generic_store.load(); _IDS = DG.DlcIds(_ST, None)
    return _ST, _IDS

def xsecs_of(name):
    from convert_dlc import raw_dlc
    raw, _ = raw_dlc(name.replace('/', '\\'))
    if raw is None: raw, _ = raw_dlc(os.path.basename(name))
    if raw is None: return None
    return sections_with_data(cdrm_decode(raw, 'be'), 'be')[1]

def analog_of(s, store, ids):
    """nearest base DTP with same size + reloc layout and a PC twin of the same size: (xbox id, xbox data, pc data)"""
    xd = s['data']
    cands = DG.analog_index(store, ids).get((7, len(xd), DG._reloc_sig(s['reloc'], 'be')), ())
    best = None
    n = len(xd) // 4
    xw = struct.unpack_from('>%dI' % n, xd)
    for x in cands:
        ad = store['xb_store'][7, x]['data']
        pd = store['pc_store'][7, ids.base[7][x]]['data']
        if len(pd) != len(ad): continue
        d = sum(1 for a, b in zip(xw, struct.unpack_from('>%dI' % n, ad)) if a != b)
        if best is None or d < best[0]: best = (d, x, ad, pd)
    return best

def pairs(xs, D, ids):
    pool = collections.defaultdict(list)
    for k, o in enumerate(D.sections): pool[o.type, o.id].append(k)
    for s in xs:
        if s['type'] != 7 or s['data'] is None: continue
        lst = pool.get((7, ids(7, s['id'])))
        if not lst: continue
        k = lst.pop(0)
        yield s, k

def candidates(xs, D, ids, store):
    xdtp = {s['id'] for s in xs if s['type'] == 7}
    out = []
    for s, k in pairs(xs, D, ids):
        pdat = D.sections[k].data
        if len(pdat) != len(s['data']): continue
        rel = R.parse(s['reloc'], 'be')
        skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
        xd = s['data']; an = None; pcb = None; tw = None
        if s['id'] in ids.base.get(7, {}):
            rec = store['pc_store'].get((7, ids.base[7][s['id']]))
            xb = store['xb_store'].get((7, s['id']))
            if rec is not None and len(rec['data']) == len(xd): pcb = rec['data']
            elif rec is not None and xb is not None and len(xb['data']) == len(rec['data']): tw = (xb['data'], rec['data'])
        for o in range(0, len(xd) - 3, 4):
            if o in skip: continue
            xv = struct.unpack_from('>I', xd, o)[0]
            if xv not in xdtp: continue
            want = ids(7, xv)
            if want == xv: continue
            pv = struct.unpack_from('<I', pdat, o)[0]
            st = status(xv, pv, want, ids)
            c = dict(sec=s['id'], k=k, off=o, xv=xv, want=want, pv=pv, st=st)
            if pcb is not None:
                c['pcw'] = struct.unpack_from('<I', pcb, o)[0]
            elif tw is not None:
                # base id, other size: the base Xbox/PC twin of the SAME id is the slot reference (where it reaches)
                if o + 4 <= len(tw[0]):
                    bxv = struct.unpack_from('>I', tw[0], o)[0]; bpv = struct.unpack_from('<I', tw[1], o)[0]
                    bm = ids.base[7].get(bxv)
                    c['twin'] = (s['id'], bxv, bpv)
                    c['tclass'] = 'id' if bm is not None and bm != bxv and bpv == bm else 'noid'
            else:
                if an is None: an = analog_of(s, store, ids) or False
                if an:
                    d, ax, ad, pd = an
                    axv = struct.unpack_from('>I', ad, o)[0]; apv = struct.unpack_from('<I', pd, o)[0]
                    am = ids.base[7].get(axv)
                    c['analog'] = (ax, d, axv, apv)
                    c['aclass'] = ('id' if am is not None and am != axv and apv == am else
                                   'same_id_raw' if apv == axv and am is not None and am != axv else
                                   'u16' if apv == u16p(axv) and axv != u16p(axv) else
                                   's32' if apv == struct.unpack('<I', struct.pack('>I', axv))[0] else
                                   'idsame' if am == axv and apv == axv else 'other')
            if 'pcw' not in c and c.get('aclass') is None and c.get('tclass') is None and c['st'] != 'ok':
                c['local'] = local_analog(xd, o, store, ids)
                c['mates'] = fieldmates(xd, rel, o, xdtp)
            out.append(c)
    return out

_BASE = None
def base_pairs(store, ids):
    """[(xbox id, xbox data, pc data)] of base DTPs with a same-size PC twin"""
    global _BASE
    if _BASE is None:
        _BASE = []
        for (t, x), xb in store['xb_store'].items():
            if t != 7: continue
            p = ids.base[7].get(x)
            pc = store['pc_store'].get((7, p)) if p is not None else None
            if pc is not None and len(pc['data']) == len(xb['data']): _BASE.append((x, xb['data'], pc['data']))
    return _BASE

LW = 4      # local-analog window: LW words before + LW words after the candidate word
def local_analog(xd, o, store, ids):
    """base DTPs whose Xbox words around o (LW before, LW after; the word itself may differ) equal the DLC words:
    slot evidence where no whole-section analog exists.  Returns Counter of the PC class at the matching word
    ('id' = base Xbox word there is a remapped DTP id and PC stores the remapped id; 'noid:<cls>' otherwise)."""
    a, b = o - 4 * LW, o + 4 + 4 * LW
    if a < 0 or b > len(xd): return None
    pre, post = xd[a:o], xd[o + 4:b]
    ws = struct.unpack('>%dI' % (2 * LW), pre + post)
    if len({w for w in ws if w}) < 3: return None          # window too generic
    c = collections.Counter()
    for x, bx, bp in base_pairs(store, ids):
        i = bx.find(pre)
        while i >= 0:
            q = i + 4 * LW
            if q % 4 == 0 and bx[q + 4:q + 4 + 4 * LW] == post:
                bxv = struct.unpack_from('>I', bx, q)[0]; bpv = struct.unpack_from('<I', bp, q)[0]
                m = ids.base[7].get(bxv)
                if m is not None and m != bxv and bpv == m: c['id'] += 1
                else: c['noid:' + status(bxv, bpv, m if m is not None else -1, ids)] += 1
            i = bx.find(pre, i + 1)
    return c

VE_MIN, VE_FRAC = 5, 0.9
FIXABLE = ('noremap', 'u16', 'byteraw')
def classify(c, store=None, ids=None):
    """first pass. REAL:* = fix (pv := want), FP:* = false positive, REVIEW:* = not decidable here (left alone);
    second pass (classify2) may upgrade REVIEW:value_* / REVIEW:local_mixed via same-section / sibling evidence."""
    if c['st'] == 'ok': return 'ok'
    if 'pcw' in c: return 'FP:pc_same' if c['pv'] == c['pcw'] else 'REVIEW:pc_differs'
    if c.get('aclass') is not None and c['aclass'] != 'id': return 'FP:analog_' + c['aclass']
    if c['st'] not in FIXABLE: return 'REVIEW:' + c['st']
    if c.get('aclass') == 'id': return 'REAL:analog'
    if c.get('tclass') == 'id': return 'REAL:twin'
    if c.get('tclass') == 'noid': return 'FP:twin_noid'
    la = c.get('local')
    if la:
        nid = sum(v for k, v in la.items() if k != 'id')
        if la['id'] and not nid: return 'REAL:local'
        if nid and not la['id']: return 'FP:local_' + la.most_common(1)[0][0]
    if c['st'] == 'u16': return 'REVIEW:u16_value_only'      # u16 needs slot-level evidence (costume 21090 vs 12649)
    n, r = value_evidence(c['xv'], *(ctx() if store is None else (store, ids)))
    c['ve'] = (n, r)
    fm = c.get('mates')
    if fm and fm[0] >= 20 and fm[1] < 0.2 * fm[0]: return 'FP:index_field'     # see fieldmates()
    if (n >= VE_MIN and r >= VE_FRAC * n) or (n >= 2 and r == n): return 'REAL:value'
    if n and r < 0.5 * n: return 'FP:value'
    return 'REVIEW:local_mixed' if la else 'REVIEW:value_mixed'

def fieldmates(xd, rel, o, xdtp, maxkey=0x40):
    """index-field veto: key = distance of o from the nearest preceding pointer slot; mates = words at the same key
    after every other pointer slot of the section.  Returns (n mates with a small non-zero int, n of them that are DTP
    ids of the same DRM) or None.  Nav/path node records {ptr, u32 index, 0, f32 xyz ..} (dlc_dungeon 20256: 817, 818,
    .. 876) carry sequential indices that sometimes equal a DTP id: their mates are mostly NOT ids."""
    import bisect
    ps = sorted(set(rel.pointer_offsets()))
    i = bisect.bisect_left(ps, o) - 1
    if i < 0: return None
    key = o - ps[i]
    if key > maxkey: return None
    n = nid = 0
    for p in ps:
        q = p + key
        if q == o or q + 4 > len(xd) or q in ps: continue
        if bisect.bisect_left(ps, q) and ps[bisect.bisect_left(ps, q) - 1] != p: continue   # another ptr in between
        v = struct.unpack_from('>I', xd, q)[0]
        if 0 < v < 0x10000:
            n += 1; nid += v in xdtp
    return n, nid

def classify2(cs, sigs):
    """same-section: a word whose value is a slot-confirmed REAL id elsewhere in the SAME section (lists of ids);
    sibling: same offset REAL in a DTP of the same DRM with the same size + reloc layout (sigs: sec -> signature)."""
    real = [c for c in cs if c['cls'].startswith('REAL:')]
    slotv = {(c['sec'], c['xv']) for c in real if c['cls'] in ('REAL:analog', 'REAL:twin', 'REAL:local')}
    sib = {(sigs.get(c['sec']), c['off']) for c in real}
    for c in cs:
        if not c['cls'].startswith('REVIEW:') or c['st'] not in FIXABLE: continue
        if c['cls'] == 'REVIEW:u16_value_only': continue
        fm = c.get('mates')
        if fm and fm[0] >= 20 and fm[1] < 0.2 * fm[0]: continue
        if (c['sec'], c['xv']) in slotv: c['cls'] = 'REAL:section'
        elif (sigs.get(c['sec']), c['off']) in sib and sigs.get(c['sec']) is not None: c['cls'] = 'REAL:sibling'

def load_overlay(dirs, names=None):
    files = {}
    for d in dirs:
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.endswith('.drm'):
                    rel = os.path.relpath(os.path.join(r, f), d).replace('\\', '/')
                    files[rel] = os.path.join(r, f)
    if names: files = {n: p for n, p in files.items() if n in names or os.path.basename(n) in names}
    return files

def scan(dirs, names=None, verbose=True):
    store, ids = ctx()
    res = {}
    for rel, path in sorted(load_overlay(dirs, names).items()):
        xs = xsecs_of(rel)
        if xs is None: continue
        D = DW.read(open(path, 'rb').read(), 'le'); ids.local = {}
        cs = candidates(xs, D, ids, store)
        cs = [c for c in cs if c['st'] != 'ok']
        if not cs: continue
        for c in cs: c['cls'] = classify(c, store, ids)
        sigs = {q['id']: (len(q['data']), DG._reloc_sig(q['reloc'], 'be')) for q in xs if q['type'] == 7 and q['data'] is not None}
        classify2(cs, sigs)
        res[rel] = (path, cs)
        if verbose:
            cnt = collections.Counter((c['sec'], c['st'], c['cls']) for c in cs)
            print(rel, '<-', path)
            for (sec, st, cl), n in sorted(cnt.items()):
                if cl == 'FP:pc_same' and not verbose > 1: continue
                ex = [c for c in cs if (c['sec'], c['st'], c['cls']) == (sec, st, cl)][:4]
                print('   DTP %-6d %-8s %-20s x%-3d' % (sec, st, cl, n),
                      [(hex(e['off']), e['xv'], '->%d' % e['want'], hex(e['pv'])) + tuple(e[k] if k != 'local' else dict(e[k]) for k in ('analog', 'twin', 'local', 've', 'mates') if e.get(k)) for e in ex])
    return res

def patch_file(rel, path, verbose=True):
    """typed fixes on one installed DRM: dtplist + align SPECS + goo block (tools/dtp_align_fix.py), then every REAL
    sweep word := ids(7, xv) (LE u32).  Returns (new raw bytes or None, Counter, [(sec, off, old, new, cls)])."""
    import dtp_align_fix as AF
    store, ids = ctx()
    xs = xsecs_of(rel)
    raw = open(path, 'rb').read()
    D = DW.read(raw, 'le'); ids.local = {}
    st = collections.Counter(); log = []
    for s, k in pairs(xs, D, ids):
        sec = D.sections[k]
        if len(sec.data) != len(s['data']): continue
        rel_ = R.parse(s['reloc'], 'be'); b = bytearray(sec.data)
        n = AF.dtplist_fix(s['data'], rel_, b, ids)
        if n: st['dtplist_words'] += n; log.append((s['id'], 'dtplist', n))
        sp = AF.SPECS.get((os.path.basename(rel), s['id']))
        if sp:
            n, eq, ex = AF.align_fix(s['data'], rel_, b, sp, store, ids)
            st['align_words'] += n; log.append((s['id'], 'align base %d/pc %d: %d equal words, %d extra' % (sp['base'], sp['pc'], eq, ex), n))
        n = AF.goo_fix(s['data'], rel_, b, store, ids)
        if n: st['goo_words'] += n; log.append((s['id'], 'goo', n))
        sec.data = bytes(b)
    cs = [c for c in candidates(xs, D, ids, store) if c['st'] != 'ok']
    for c in cs: c['cls'] = classify(c, store, ids)
    sigs = {q['id']: (len(q['data']), DG._reloc_sig(q['reloc'], 'be')) for q in xs if q['type'] == 7 and q['data'] is not None}
    classify2(cs, sigs)
    byk = collections.defaultdict(list)
    for c in cs:
        st['cls ' + c['cls']] += 1
        if c['cls'].startswith('REAL:'): byk[c['k']].append(c)
    for k, lst in byk.items():
        b = bytearray(D.sections[k].data)
        for c in lst:
            b[c['off']:c['off'] + 4] = struct.pack('<I', c['want']); st['id_words'] += 1
            log.append((c['sec'], 'id %#x %d: %#x -> %d (%s %s)' % (c['off'], c['xv'], c['pv'], c['want'], c['st'], c['cls']), 1))
        D.sections[k].data = bytes(b)
    if not (st['dtplist_words'] + st['align_words'] + st['goo_words'] + st['id_words']): return None, st, log
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    return out, st, log

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'scan':
        dirs = sys.argv[2].split(','); names = set(sys.argv[3:]) or None
        res = scan(dirs, names)
        tot = collections.Counter(c['cls'] for _, cs in res.values() for c in cs)
        print('TOTAL', dict(tot))
    elif cmd == 'patch':
        import hashlib
        out_dir, dirs, names = sys.argv[2], sys.argv[3].split(','), sys.argv[4:]
        files = load_overlay(dirs)
        for name in names:
            path = files.get(name)
            if path is None: print(name, 'not found'); continue
            new, st, log = patch_file(name, path)
            print(name, '<-', path, {k: v for k, v in st.items()})
            for sec, what, n in log: print('   DTP', sec, what, n)
            if new is not None:
                op = os.path.join(out_dir, name); os.makedirs(os.path.dirname(op), exist_ok=True)
                open(op, 'wb').write(new); print('   wrote', op, hashlib.md5(new).hexdigest())
