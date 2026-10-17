"""unbound_fix (ws/glass): PC pixel-shader sampler registers that the material does not bind.

Defect class: the converted DLC material uses a *surrogate* PC shader lib (material_dlc 'base_material' choice) that samples
a register for which the Xbox material has no texture entry (e.g. cube environment map, ty4). On PC the sampler stays unbound
(stale / undefined texture). Calibration: 0 of 2248 PC base materials have such a register (PM, material_reslot.libs()).

CLI (run with tools/venv/bin/python -I):
  unbound_fix.py scan  ROOT            list (drm, material, unbound regs, kind) over every .drm under ROOT (mods folder)
  unbound_fix.py fix   SRC.drm OUT.drm [--mats 20265,23397] [--cube 569] [--coload]   write a NEW drm (only the listed materials; default: all
                                       fixable = unbound CUBE regs with a free cube texture available in the same DRM)
Library: unbound(pd, pr) -> ([(reg, names, kind)], pc_tuple); insert_entry(pd, pr, index, tid, ty, slot, bias, filt, counts=True)
         fix_section(pd, pr, cube_ids) -> (pd2, pr2, [log]) or None
Only CUBE sampler registers are fixed (dark cube bound as ty4 at that register, entry bytes copied from base PC / sibling cube entries).
2D unbound registers are reported, not fixed (semantics of the missing overlay unknown).
"""
import sys, os, struct, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, material_reslot as MR, drm_write as DW

DARK_CUBES = (569, 6549, 724, 4955)      # dark environment cubes seen bound as ty4 on PC base / sibling DLC materials (569: 37 base materials)
_L = None
def libs():
    global _L
    if _L is None: _L = MR.libs()
    return _L

def unbound(pd, pr):
    P = libs()['P']
    pt = struct.unpack_from('<4I', pd, 0x28)
    plibs = [P.get(x) if x else None for x in pt[:3]]
    keys = [('p', x) for x in pt[:3]]
    br = MR.bound_report(pd, pr, plibs, pkeys=keys)
    kinds = collections.defaultdict(set)
    for i, lib in enumerate(plibs):
        if lib is None or lib['kind'] != 1: continue
        for r, v in MR.sampler_kinds(lib, ('k',) + tuple(keys[i])).items(): kinds[r] |= v
    return [(r, sorted(ns), sorted(kinds.get(r, ()))) for r, ns, ty in br if ty is None], pt

def insert_entry(pd, pr, index, tid, ty, slot, bias=-1.0, filt=2, counts=True):
    """Insert one 16-byte texture entry at position `index` of the texture list (0x54). Returns (new data, new reloc blob)."""
    rel = R.parse(pr, 'le')
    ids = sorted(o for t, o in rel.idref + rel.idref_a if t == 5)
    T = dict(rel.internal)[0x54]
    assert ids and ids[0] == T and all(b - a == 16 for a, b in zip(ids, ids[1:])), 'texture list not contiguous'
    ins = T + 16 * index
    assert ins <= ids[-1] + 16
    entry = struct.pack('<IfIBBH', tid, bias, ty, 0, slot, filt)
    nd = bytearray(pd[:ins] + entry + pd[ins:])
    sh = lambda v: v + 16 if v >= ins else v
    nr = R.Reloc(internal=sorted((sh(a), sh(b)) for a, b in rel.internal), external=list(rel.external),
                 idref_a=sorted((t, sh(o)) for t, o in rel.idref_a), unk3=list(rel.unk3),
                 idref=sorted((t, sh(o)) for t, o in rel.idref))
    nr.idref.append((5, ins)); nr.idref.sort(key=lambda x: x[1])
    # pointers stored in data keep their placeholder; counts of sampled textures (0x51/0x52) only for real texture types
    if counts and ty not in (6, 7):
        nd[0x51] += 1; nd[0x52] += 1
    blob = R.write(nr, 'le')
    assert not R.check(R.parse(blob, 'le'), len(nd))
    return bytes(nd), blob

def fix_section(pd, pr, cube_ids=DARK_CUBES, available=None, coload=False):
    """Bind a dark cube to every unbound CUBE sampler register. available: set of texture ids present in the DRM (None: no check).
    Returns (pd2, pr2, log) or None when nothing to do."""
    u, pt = unbound(pd, pr)
    todo = [(r, ns) for r, ns, k in u if k == ['cube']]
    if not todo: return None
    log = []
    for r, ns in todo:
        cand = [c for c in cube_ids if available is None or c in available]
        coloaded = False
        if not cand and coload: cand = [cube_ids[0]]; coloaded = True      # id not in this DRM: rely on co-loaded DRM (PC base does it 418x)
        if not cand: log.append((r, 'no cube available')); continue
        es = MR.tex_entries(pd, R.parse(pr, 'le'), '<')
        # The engine (fn 0x505a90) walks THREE groups of the texture list: A/B = [0, c52) with counts 0x51/0x52, C = [c52, c52+c50) (0x50).
        # The cube sampler belongs at the END of A/B = index c52; 'count of non-6/7 entries' lands inside group C (crash 0x800001 on material
        # 23397: header (2,8,8), ty5 in group C) because the +1 on 0x51/0x52 then moves the group boundary past the ty5 entry.
        assert pd[0x51] == pd[0x52], 'unequal group counters: not handled'
        pos = pd[0x52]
        if any(e[3] == r for e in es): log.append((r, 'slot already used by an entry: skipped')); continue
        pd, pr = insert_entry(pd, pr, pos, cand[0], 4, r)
        log.append((r, 'cube %d inserted at index %d slot %d%s' % (cand[0], pos, r, ' (CO-LOAD: cube not in this DRM)' if coloaded else '')))
    return pd, pr, log

def _read(path):
    from drm import cdrm_decode, sections_with_data
    raw = cdrm_decode(open(path, 'rb').read(), 'le')
    return sections_with_data(raw, 'le')[1]

def scan(root):
    rows = []
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            if not f.endswith('.drm'): continue
            p = os.path.join(dp, f)
            try: secs = _read(p)
            except Exception: continue
            for s in secs:
                if s['type'] != 10: continue
                try: u, pt = unbound(s['data'], s['reloc'])
                except Exception: continue
                if u: rows.append((os.path.relpath(p, root), s['id'], u, pt))
    return rows

def fix_drm(src, out, mats=None, cube=None, coload=False):
    D = DW.read(open(src, 'rb').read(), 'le')
    avail = {s.id for s in D.sections if s.type == 5}
    # sanity: unmodified round trip is byte-exact w.r.t. the decoded source
    assert D.write('le') == DW.cdrm_decode(open(src, 'rb').read(), 'le'), 'round trip not exact'
    n = 0; rep = []
    for s in D.sections:
        if s.type != 10 or (mats and s.id not in mats): continue
        r = fix_section(s.data, s.reloc, (cube,) if cube else DARK_CUBES, avail, coload)
        if r is None: continue
        if r[0] == s.data and r[1] == s.reloc: continue          # nothing changed (e.g. no cube available)
        s.data, s.reloc, log = r; n += 1; rep.append((s.id, log))
    if n == 0: return 0, rep, None                           # do not write an unchanged file
    data = DW.cdrm_encode(D.write('le'), 'le')
    open(out, 'wb').write(data)
    return n, rep, hashlib.md5(data).hexdigest()

if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'scan':
        rows = scan(a[1]); mats = set()
        for f, mid, u, pt in rows: print(f, mid, u, [hex(x) for x in pt]); mats.add(mid)
        print('rows', len(rows), 'distinct materials', len(mats))
    elif a and a[0] == 'fix':
        mats = None; cube = None
        if '--mats' in a: mats = {int(x) for x in a[a.index('--mats') + 1].split(',')}
        if '--cube' in a: cube = int(a[a.index('--cube') + 1])
        print(fix_drm(a[1], a[2], mats, cube, '--coload' in a))
    else: print(__doc__)
