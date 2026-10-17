"""analog_idcoin.py - guard for dlc_generic.analog_convert / _analog_build: IDENTITY-REMAP COINCIDENCE (crash 0x5c019f, 2026-10-12).

Defect: the clone test of _analog_build accepts a differing word (analog Xbox value vb -> DLC value vd) as a section-id reference
of type T when  vb is a base id of type T  and  vd is a section of type T in THIS DRM, then writes ids(T, vd) at the slot found
by occurrence alignment (PC word == ids(T, vb)).  When ids(T, vb) == vb (identity remap, e.g. base shader 2 -> 2) the alignment
proves NOTHING: the PC word equals the Xbox word whether the slot is an id or a plain integer.  Small integers (material index,
counts, enum) then pass as 'ids' because some section of that type happens to have that number.
Case: dlc_dungeon_dungeon_main DTP 23793..23796 @0x10 (draw-list entry material index, Xbox 8): analog Xbox DTP 17740 holds 2 there,
base shader id 2 -> 2 (identity), the DRM has a shader section 8 -> ids(9, 8) = 213 written instead of 8 -> index 213 into an 11-entry
material table -> read of [table + 213*0x50 + 0x30] = 1 -> AV at 0x5c019f.
Guard: an option (T, vp) with vp == vb is accepted only if ids(T, vd) == vd for every DLC value (the write would be a no-op); otherwise it is
dropped.  If no option remains the analog is 'unaligned' (next analog / generic route).

CLI (python -I):
  tools/venv/bin/python -I tools/analog_idcoin.py selftest              leave-one-out on ALL base Xbox/PC pairs: unguarded vs guarded vs real PC bytes
  tools/venv/bin/python -I tools/analog_idcoin.py scan DIR[,DIR..]      DLC-new type-7 sections: words where guarded != unguarded, vs installed bytes
  tools/venv/bin/python -I tools/analog_idcoin.py fix OUT DIR[,DIR..]   writes the corrected DRMs (only words: installed == unguarded != guarded-final)
API: guarded(): context manager that patches dlc_generic._analog_build; convert_section(...) is dlc_generic.convert_drm's own route.
"""
import sys, os, struct, collections, hashlib, contextlib, pickle, json
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
W = os.path.normpath(os.path.join(TOOLS, '..', 'work'))
import dlc_generic as DG, drm_reloc as R

_ORIG = DG._analog_build


def _build_guarded(xd, xw, rx, ax, n, ids, store, have):
    """copy of dlc_generic._analog_build with ONE change: options with ids(T, vb) == vb are not evidence (see module doc)"""
    import numpy as np
    t = 7
    xa = store['xb_store'][t, ax]['data']; pc = store['pc_store'][t, ids.base[t][ax]]
    pa = pc['data']; rp = R.parse(pc['reloc'], 'le')
    if rp.external or rx.external: return 'ext_relocs'
    if [a for a, _ in rx.idref] != [a for a, _ in rp.idref] or [a for a, _ in rx.idref_a] != [a for a, _ in rp.idref_a]:
        return 'idref_layout'
    out = bytearray(pa)
    for lx, lp in ((rx.idref, rp.idref), (rx.idref_a, rp.idref_a)):
        for (ty, ox), (_, op) in zip(lx, lp):
            v, = struct.unpack_from('>I', xd, ox)
            struct.pack_into('<I', out, op, ids(ty, v) if v not in (0, 0xffffffff) else v)
    skx = set(rx.pointer_offsets()) | set(rx.id_offsets()); skp = set(rp.pointer_offsets()) | set(rp.id_offsets())
    aw = np.frombuffer(xa, '>u4', n); pw = np.frombuffer(pa, '<u4', len(pa) // 4)
    diff = [int(i) * 4 for i in np.nonzero(aw != xw)[0] if int(i) * 4 not in skx]
    by_val = collections.defaultdict(list)
    for o in diff: by_val[int(aw[o // 4])].append(o)
    for vb, offs in by_val.items():
        ox = [int(i) * 4 for i in np.nonzero(aw == vb)[0] if int(i) * 4 not in skx]
        vds = [struct.unpack_from('>I', xd, o)[0] for o in offs]
        opts = [(ty, m[vb]) for ty, m in sorted(ids.base.items()) if isinstance(ty, int) and ty < 100 and vb in m
                and all(v in have.get(ty, ()) for v in vds)
                and (m[vb] != vb or all(ids(ty, v) == v for v in vds))]   # <-- guard: identity remap proves nothing -> only accepted when it changes nothing
        done = False
        for ty, vp in opts:
            op = [int(i) * 4 for i in np.nonzero(pw == vp)[0] if int(i) * 4 not in skp]
            if len(op) != len(ox): continue
            dl = len(pa) - len(xa)
            if any(not (min(0, dl) <= b - a <= max(0, dl)) for a, b in zip(ox, op)): continue
            pos = dict(zip(ox, op))
            for o, vd in zip(offs, vds):
                struct.pack_into('<I', out, pos[o], ids(ty, vd))
            done = True; break
        if not done: return 'unaligned'
    return bytes(out), pc['reloc']


@contextlib.contextmanager
def guarded():
    DG._analog_build = _build_guarded
    try: yield
    finally: DG._analog_build = _ORIG


def selftest():
    """leave-one-out over all base pairs (work/generic/pairs.pkl): treat every Xbox type-7 DTP as DLC-new (own DRM's DTP ids excluded
    from the analog search), compare analog_convert output with the real PC section, unguarded vs guarded"""
    import generic_store
    store = generic_store.load(); ids = DG.DlcIds(store, None)
    pairs = pickle.load(open(os.path.join(W, 'generic', 'pairs.pkl'), 'rb'))
    res = {}
    for mode in ('unguarded', 'guarded'):
        tot = collections.Counter(); bad = []
        ctx = guarded() if mode == 'guarded' else contextlib.nullcontext()
        with ctx:
            for name, ((xh, xs), (ph, ps)) in sorted(pairs.items()):
                pm = {(s['type'], s['id']): s for s in ps}
                own = {s['id'] for s in xs if s['type'] == 7}
                ids.local = {}
                for s in xs:
                    if s['type'] != 7 or s['data'] is None: continue
                    r = DG.analog_convert(s, xs, ids, store, exclude=own)
                    if r is None: tot['no_analog'] += 1; continue
                    q = pm.get((7, ids.base[7].get(s['id'])))
                    if q is None or q['data'] is None: tot['no_pc'] += 1; continue
                    data = r[0]
                    if data == q['data']: tot['exact'] += 1
                    else:
                        tot['wrong'] += 1
                        nw = sum(data[i:i + 4] != q['data'][i:i + 4] for i in range(0, min(len(data), len(q['data'])), 4)) if len(data) == len(q['data']) else -1
                        tot['wrong_words'] += max(nw, 0)
                        bad.append((name, s['id'], r[2], nw))
        res[mode] = (dict(tot), bad)
        print(mode, dict(tot), 'wrong sections:', len(bad))
    ub, gb = {(a, b) for a, b, _, _ in res['unguarded'][1]}, {(a, b) for a, b, _, _ in res['guarded'][1]}
    print('wrong only guarded:', sorted(gb - ub)[:20], len(gb - ub), '| wrong only unguarded:', sorted(ub - gb)[:20], len(ub - gb))
    return res


def _installed(dirs):
    import dtp_audit as A
    return A.overlay([d if os.path.isabs(d) else os.path.join(W, d) for d in dirs])


def scan(dirs, with_fix=None):
    """for each DLC-new type-7 section routed 'analog' (unguarded): guarded final value (analog_convert guarded, else generic route) per word.
    Returns rows (file, sec id, offset, xbox, unguarded, guarded_final, installed)"""
    import dtpid_sweep as DS, dtp_audit as A, drm_write as DW
    st, ids = DS.ctx(); G0 = DG._G0(); T = DG.table(); rows = []; ntot = nan = 0
    for rel, path in sorted(_installed(dirs).items()):
        xs = A.xsecs(rel)
        if xs is None: continue
        ids.local = {}
        D = DW.read(open(path, 'rb').read(), 'le'); labs0 = None
        for x, i in A.section_pairs(xs, D):
            if x['type'] != 7 or x['id'] in ids.base.get(7, {}): continue
            ntot += 1
            ru = DG.analog_convert(x, xs, ids, st, ())
            if ru is None: continue
            nan += 1
            with guarded(): rg = DG.analog_convert(x, xs, ids, st, ())
            if rg is not None and rg[0] == ru[0]: continue
            if labs0 is None: labs0 = G0.labels(xs, 'be')
            k = xs.index(x)
            fin = rg[0] if rg is not None else G0.convert_section0(x['data'], labs0[k], R.parse(x['reloc'], 'be'), G0.table7(), ids, T)
            sec = D.sections[i]
            if not (len(fin) == len(ru[0]) == len(sec.data)):
                rows.append(dict(file=rel, sec=sec.id, off=-1, note='size differs between routes %d/%d/%d' % (len(fin), len(ru[0]), len(sec.data)))); continue
            for w in range(0, len(fin) - 3, 4):
                if fin[w:w + 4] != ru[0][w:w + 4]:
                    rows.append(dict(file=rel, sec=sec.id, off=w, xbox=struct.unpack_from('>I', x['data'], w)[0], unguarded=struct.unpack_from('<I', ru[0], w)[0],
                                     guarded=struct.unpack_from('<I', fin, w)[0], installed=struct.unpack_from('<I', sec.data, w)[0],
                                     route='analog' if rg is not None else 'generic'))
    print('DLC-new type-7 sections', ntot, 'analog route', nan, 'delta words', sum(1 for r in rows if r['off'] >= 0))
    return rows


def fix(out, dirs):
    import drm_write as DW
    rows = [r for r in scan(dirs) if r['off'] >= 0 and r['installed'] == r['unguarded']]       # only words still holding the unguarded value
    by = collections.defaultdict(list)
    for r in rows: by[r['file']].append(r)
    files = _installed(dirs); md5 = []; log = []
    for rel, rs in sorted(by.items()):
        raw = open(files[rel], 'rb').read(); D = DW.read(raw, 'le')
        for r in rs:
            sec = [s for s in D.sections if s.type == 7 and s.id == r['sec']][0]
            b = bytearray(sec.data); struct.pack_into('<I', b, r['off'], r['guarded']); sec.data = bytes(b)
            log.append('%s\t%d\t0x%x\t%d\t%d' % (rel, r['sec'], r['off'], r['installed'], r['guarded']))
        o = D.write('le')
        if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
        D2 = DW.read(o, 'le'); D0 = DW.read(raw, 'le')
        assert len(D0.sections) == len(D2.sections) and D0.names == D2.names
        for a0, a2 in zip(D0.sections, D2.sections): assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
        md5.append('%s  %s' % (hashlib.md5(o).hexdigest(), rel))
    open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
    open(os.path.join(out, 'words.tsv'), 'w').write('file\tdtp\toff\tinstalled\tcorrected\n' + '\n'.join(log) + '\n')
    print('\n'.join(md5)); return md5


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == 'selftest': selftest()
    elif a[0] == 'scan':
        rows = scan(a[1].split(','))
        for r in rows: print(json.dumps(r))
    elif a[0] == 'fix': fix(a[1], a[2].split(','))
