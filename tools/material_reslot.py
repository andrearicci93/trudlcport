"""Texture-slot re-binding for DLC materials whose pixel shaders were replaced by PC surrogates.

Problem (glitch 'green translucent volume' in dlc_caverns, 2026-10-10):
  A material texture entry (16 B: u32 texId, u32 lodBias?, u32 type, u8 flag, u8 SLOT, u16 filter) is bound to the
  pixel-shader SAMPLER REGISTER = SLOT (base PC materials: 15550/16400 entries sit on a sampler register of the
  material's PS libs; every sampler NAME takes a single entry 'type' in 298/299 names; Xbox and PC keep the register of a
  name). material_dlc copied the Xbox slots 1:1, but for 'converted' DLC materials with C1/C2/C3/D surrogate PS libs the
  PC lib's sampler layout differs (C3 = only the register SET matches).  205/587 converted materials bind at least one
  texture to a register whose PC sampler has another name; e.g. dlc_caverns 23329/23173/20673/20676 put a DXN normal map
  (PC DXT5: R=x, G=255, B=0, A=y) on a 'Material_*_Texture' colour sampler -> lime-green, half transparent surfaces.

Rule (per converted material; only the slot byte changes, section size/relocs unchanged):
  1. entry whose Xbox sampler name(s) at its slot also exist at the SAME register of the PC PS libs -> kept;
  2. else move to a free PC register carrying one of its Xbox sampler names (exact name match);
  3. else move to a free PC register whose expected entry TYPE equals the entry type (expected type per register:
     surrogate base PC material's entries, else the PC name->type table learnt from base PC materials), preferring
     the most shared name tokens, then the closest register;
  4. else (no certainty): 4a back to the XBOX slot if still free and not a hard mismatch (cube<->2D sampler from
     the PS dcl_* tokens, normal map on non-Normal sampler / other on Normal sampler) [2026-10-10, mods_glitchfix2:
     the first rule parked such entries and EMPTIED PC samplers that fix14 fed, e.g. grapple mount 20344/21093
     Param + BackBufferTexture]; 4b park on an unsampled register / 'fill' an unbound sampler (compatible first);
     4c an empty PC sampler that the Xbox slots fed gets a parked compatible entry ('refill').
     --old reproduces mods_glitchfix.
Registers sampled only by engine samplers (shadow/attenuation/modulation) are never targets.

API:  reslot(xd, xr, pd, pr, xlibs, plibs, ref=None) -> (new pc data, changes)   (xlibs/plibs: PS libs of passes 0..2)
      patch_drm(raw_le_drm_bytes) -> (new raw bytes or None, report)
CLI:  tools/venv/bin/python -I tools/material_reslot.py validate         (base-pair checks, see validate())
      tools/venv/bin/python -I tools/material_reslot.py patch OUT SRC.drm [SRC2.drm ..]   (writes only changed files)
"""
import sys, os, struct, pickle, json, collections, re, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import drm_write as DW
from shaderlib import constants
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')
FALLBACK = True          # False = first rule (work/mods_glitchfix); CLI --old
ENGINE = {'ShadowMapSampler', 'AttenuationSampler', 'ModulationMaps', 'ModulationMapSamplers'}

_L = None
def libs():
    global _L
    if _L is None:
        _L = pickle.load(open(os.path.join(W, 'shaderlibs.pkl'), 'rb'))
    return _L

_RM = {}
def regmap(lib, plat, key=None):
    """{register: set(sampler names)} over all permutations of a PS lib."""
    if key is not None and key in _RM: return _RM[key]
    res = collections.defaultdict(set)
    if lib is not None and lib['kind'] == 1:
        for s in set(lib['slots']) - {0xFFFFFFFF}:
            v, c = constants(lib['entries'][s]['blob'], plat)
            for n, rs, ri, rc in c:
                if rs == 3:
                    for k in range(rc): res[ri + k].add(n)
    res = dict(res)
    if key is not None: _RM[key] = res
    return res

_SK = {}
def sampler_kinds(lib, key=None):
    """{register: set('2d'|'cube'|'vol')} from the dcl_* sampler declarations of a PC (D3D9 SM3) PS lib, all
    permutations (same register set as the CTAB, but carries the texture TYPE: a cube texture on a 2D sampler, or a
    2D texture on a cube sampler, samples garbage/black)."""
    if key is not None and key in _SK: return _SK[key]
    res = collections.defaultdict(set)
    if lib is not None and lib['kind'] == 1:
        for s in set(lib['slots']) - {0xFFFFFFFF}:
            b = lib['entries'][s]['blob']; n = len(b) // 4
            t = struct.unpack_from('<%dI' % n, b, 0); i = 1
            while i < n:
                tok = t[i]; op = tok & 0xFFFF
                if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
                if op == 0xFFFF: break
                if op == 0x1F and i + 2 < n:
                    r = t[i + 2]
                    if (((r >> 28) & 7) | ((r >> 8) & 0x18)) == 10:
                        res[r & 0x7FF].add({2: '2d', 3: 'cube', 4: 'vol'}.get((t[i + 1] >> 27) & 0xF, '?'))
                i += 1 + ((tok >> 24) & 0xF)
    res = dict(res)
    if key is not None: _SK[key] = res
    return res

def tex_entries(d, rel, e):
    """[(offset, texId, type, slot)] in reloc order (type-5 id refs)."""
    return [(o, struct.unpack_from(e + 'I', d, o)[0], struct.unpack_from(e + 'I', d, o + 8)[0], d[o + 13])
            for t, o in sorted(rel.idref + rel.idref_a, key=lambda x: x[1]) if t == 5]

def _tokens(n):
    return set(x for x in re.split(r'_', n) if len(x) >= 6)

_NT = None
def name_type():
    """PC sampler name -> majority texture entry type, learnt from base PC materials."""
    global _NT
    if _NT is None:
        L = libs(); P, PM = L['P'], L['PM']
        c = collections.defaultdict(collections.Counter)
        for pid, (d, r) in PM.items():
            regs = union_regs([P.get(s) for s in struct.unpack_from('<4I', d, 0x28)[:3]], 'p',
                              keys=[('p', s) for s in struct.unpack_from('<4I', d, 0x28)[:3]])
            for o, tid, ty, slot in tex_entries(d, R.parse(r, 'le'), '<'):
                for n in regs.get(slot, ()): c[n][ty] += 1
        _NT = {n: v.most_common(1)[0][0] for n, v in c.items()}
    return _NT

def union_regs(lib_list, plat, keys=None):
    out = collections.defaultdict(set)
    for i, lib in enumerate(lib_list):
        if lib is None or lib['kind'] != 1: continue
        for k, v in regmap(lib, plat, keys[i] if keys else None).items(): out[k] |= v
    return dict(out)

def compute_slots(xd, xr, xlibs, plibs, ref=None, xkeys=None, pkeys=None, use_names=True, fallback=True):
    """New PC slot per Xbox texture entry (Xbox entry order). Returns [(texId, type, old slot, new slot, how)].
    fallback=False reproduces the first (mods_glitchfix) rule."""
    xreg = union_regs(xlibs, 'x', xkeys)
    preg = union_regs(plibs, 'p', pkeys)
    kinds = collections.defaultdict(set)
    for i, lib in enumerate(plibs):
        for r, v in sampler_kinds(lib, ('k',) + tuple(pkeys[i]) if pkeys else None).items(): kinds[r] |= v
    def compatible(r, ty):
        """hard type check of entry type ty on PC register r (base PC: type 4 <-> cube sampler 375/375; type 3 on
        Normal samplers)."""
        if 'cube' in kinds.get(r, ()) and ty != 4: return False
        if ty == 4 and kinds.get(r) and 'cube' not in kinds[r]: return False
        nrm = any(n.startswith('p_default_Normal') for n in preg.get(r, ()))
        if (ty == 3) != nrm and r in preg: return False
        return True
    xe = tex_entries(xd, R.parse(xr, 'be'), '>')
    nt = name_type()
    exp = {}                                     # expected entry type per PC register
    if ref is not None:
        for o, tid, ty, slot in tex_entries(ref[0], R.parse(ref[1], 'le'), '<'): exp.setdefault(slot, ty)
    for r, ns in preg.items():
        if r not in exp:
            ts = {nt[n] for n in ns if n in nt}
            if len(ts) == 1: exp[r] = ts.pop()
    targets = {r for r, ns in preg.items() if ns - ENGINE}
    n = len(xe); new = [None] * n; how = [None] * n; taken = set()
    xn = [xreg.get(slot, set()) for _, _, _, slot in xe]
    # 1. keep entries already on a register with one of their names (or not sampled at all on either side)
    for k, (o, tid, ty, slot) in enumerate(xe):
        ok = (use_names and xn[k] & preg.get(slot, set())) or (not xn[k] and slot not in targets)
        if ok:
            new[k] = slot; how[k] = 'keep'; taken.add(slot)
    # 1b. names unavailable (C3/D-like): keep entries whose current register expects their type
    for k, (o, tid, ty, slot) in enumerate(xe):
        if new[k] is None and slot in targets and slot not in taken and exp.get(slot) == ty and \
                not (use_names and xn[k] and any(xn[k] & preg[r] for r in targets)):
            if use_names and xn[k] & set().union(*[preg[r] for r in targets]): continue
            if use_names and xn[k] and preg.get(slot) and not xn[k] & preg[slot] and \
                    any(n in set().union(*[xreg.get(r, set()) for r in xreg]) for n in preg[slot]): continue
            new[k] = slot; how[k] = 'keep-type'; taken.add(slot)
    # 2. exact name match on another register
    if use_names:
        for k, (o, tid, ty, slot) in enumerate(xe):
            if new[k] is not None or not xn[k]: continue
            c = sorted(r for r in targets - taken if xn[k] & preg[r])
            if c:
                r = min(c, key=lambda r: abs(r - slot)); new[k] = r; how[k] = 'name'; taken.add(r)
    # 3. entry type match (+ shared name tokens)
    for k, (o, tid, ty, slot) in enumerate(xe):
        if new[k] is not None: continue
        c = [r for r in targets - taken if exp.get(r) == ty]
        if c:
            xt = set().union(*[_tokens(x) for x in xn[k]]) if xn[k] else set()
            r = max(c, key=lambda r: (len(xt & set().union(*[_tokens(x) for x in preg[r]])), r == slot, -abs(r - slot)))
            new[k] = r; how[k] = 'type'; taken.add(r)
    # 4. no PC sampler for this entry (no name, no type evidence).
    # 4a. (2026-10-10 fix, conservative) FALL BACK TO THE XBOX SLOT when it is still free, also if a PC sampler of
    #     another name reads it, as long as the binding is not a hard mismatch (cube <-> 2D sampler, normal map on a
    #     non-Normal sampler, other texture on a Normal sampler).  The old rule parked these entries on an unsampled
    #     register and left the PC sampler EMPTY (stale/black texture): e.g. dlc1_ei_grapple_ceiling/_wall mount
    #     20344/21093 lost the textures of their Param (reg 4) and BackBufferTexture (reg 6) samplers, which the Xbox
    #     slots (= fix14) did feed.  Done for all remaining entries before any parking, so 'fill' cannot steal them.
    if fallback:
        for k, (o, tid, ty, slot) in enumerate(xe):
            if new[k] is not None or slot in taken or slot not in targets: continue
            if compatible(slot, ty):
                new[k] = slot; how[k] = 'xbox'; taken.add(slot)
    # 4b. stay if the register is free and not sampled by another PC sampler, else move
    #    to the lowest free register no PC sampler reads (what PC itself does, e.g. base material 5713 -> PC 6076)
    #    (base pairs: 7848/8107 etc.); if every register is in use, fill a PC sampler that no entry feeds (better than
    #    leaving two entries on one register: the later one would override the right texture)
    for k, (o, tid, ty, slot) in enumerate(xe):
        if new[k] is not None: continue
        if slot not in taken and slot not in targets:
            new[k] = slot; how[k] = 'unchanged'
        else:
            free = [r for r in range(16) if r not in taken and r not in preg]
            unbound = sorted(targets - taken)
            if free:
                new[k] = free[0]; how[k] = 'parked'
            elif unbound:
                ok = ([r for r in unbound if compatible(r, ty)] if fallback else []) or unbound   # compatible first
                new[k] = min(ok, key=lambda r: (exp.get(r) != ty, abs(r - slot))); how[k] = 'fill'
            else:
                new[k] = slot; how[k] = 'conflict'
        taken.add(new[k])
    # 4c. never leave EMPTY a PC sampler that the Xbox slots (fix14) fed: give it a parked entry (one no PC sampler
    #     reads anyway), type-compatible, expected type first, then the nearest Xbox slot.
    if fallback:
        xslots = {slot for _, _, _, slot in xe}
        for r in sorted(targets - set(new)):
            if r not in xslots: continue
            c = [k for k in range(n) if how[k] == 'parked' and compatible(r, xe[k][2])]
            if c:
                k = min(c, key=lambda k: (exp.get(r) != xe[k][2], abs(xe[k][3] - r)))
                new[k] = r; how[k] = 'refill'
    return [(tid, ty, slot, new[k], how[k]) for k, (o, tid, ty, slot) in enumerate(xe)]

def reslot(xd, xr, pd, pr, xlibs, plibs, ref=None, xkeys=None, pkeys=None, use_names=True, fallback=None):
    """xd/xr: Xbox material (BE) ; pd/pr: converted PC material (LE, texture entries in Xbox order as written by
    material_convert). Returns (new pd bytes, [(texId, type, old slot, new slot, how)])."""
    ch = compute_slots(xd, xr, xlibs, plibs, ref, xkeys, pkeys, use_names, FALLBACK if fallback is None else fallback)
    pe = tex_entries(pd, R.parse(pr, 'le'), '<')
    assert len(ch) == len(pe), (len(ch), len(pe))
    out = bytearray(pd)
    for (o, tid, ty, slot), c in zip(pe, ch):
        assert ty == c[1] and slot == c[2], 'PC entry order differs from Xbox'
        out[o + 13] = c[3]
    return bytes(out), [(tid,) + c[1:] for (o, tid, ty, slot), c in zip(pe, ch)]

def bound_report(pd, pr, plibs, pkeys=None):
    """[(register, PC sampler names, entry type or None)] for every non-engine PC sampler register."""
    preg = union_regs(plibs, 'p', pkeys)
    by = {slot: ty for o, tid, ty, slot in tex_entries(pd, R.parse(pr, 'le'), '<')}
    return [(r, ns, by.get(r)) for r, ns in sorted(preg.items()) if ns - ENGINE]

# ------------------------------------------------------------------------------------------------ DLC materials
_DLC = None
def dlc_tables():
    global _DLC
    if _DLC is None:
        mats = pickle.load(open(os.path.join(W, 'dlc_materials_pc.pkl'), 'rb'))
        msh = {int(k): v for k, v in json.load(open(os.path.join(W, 'dlc_material_shaders.json'))).items()}
        mx2p = pickle.load(open(os.path.join(W, 'material_x2p.pkl'), 'rb'))
        _DLC = (mats, msh, mx2p)
    return _DLC

def dlc_reslot(xmid, pd, pr):
    """Re-slot one converted DLC material (installed PC bytes pd/pr). Returns (new pd, changes) or (pd, None) if the
    material is not a converted one."""
    L = libs(); X, D, P, PM, DM = L['X'], L['D'], L['P'], L['PM'], L['DM']
    mats, msh, mx2p = dlc_tables()
    m = mats.get(xmid)
    if m is None or m['source'] != 'converted' or xmid not in DM: return pd, None
    xd, xr = DM[xmid]
    xt = struct.unpack_from('>4I', xd, 0x28); pt = struct.unpack_from('<4I', pd, 0x28)
    if list(pt) != list(m['pc_tuple']) or len(pd) != len(m['data']): return pd, None     # not this DLC material
    XL = lambda s: D.get(s, X.get(s)) if s else None
    xlibs = [XL(s) for s in xt[:3]]; plibs = [P.get(s) if s else None for s in pt[:3]]
    bm = msh.get(xmid, {}).get('base_material')
    ref = PM.get(mx2p.get(bm)) if bm is not None else None
    return reslot(xd, xr, pd, pr, xlibs, plibs, ref, xkeys=[('x', s) for s in xt[:3]], pkeys=[('p', s) for s in pt[:3]])

def patch_drm(raw):
    """raw: PC DRM (CDRM or raw, LE). Re-slots every converted DLC material section. Returns (new raw DRM or None, report)."""
    Dr = DW.read(raw, 'le')
    rep = []; changed = False
    for s in Dr.sections:
        if s.type != 10: continue
        nd, ch = dlc_reslot(s.id, s.data, s.reloc)
        if ch is None: continue
        moved = [c for c in ch if c[2] != c[3]]
        if moved:
            s.data = nd; changed = True
        rep.append((s.id, moved, [c for c in ch if c[4] == 'unchanged']))
    return (Dr.write('le') if changed else None), rep

# ------------------------------------------------------------------------------------------------ validation
SLOT_ONLY = False
def validate():
    """Base pairs (Xbox material -> real PC material): PC re-assigns entries to the registers of its own PS libs, so the
    truth is the set {(PC texture id, type, flag, slot)} of the PC material.
    (a) names available: rule on the real Xbox/PC lib pair (A/B/C1/C2-like);
    (b) names withheld (C3/D-like): type matching only, reference = ANOTHER base PC material with the same PC tuple;
    baseline = Xbox slots copied (what material_dlc did)."""
    L = libs(); X, P, XM, PM = L['X'], L['P'], L['XM'], L['PM']
    mx2p = pickle.load(open(os.path.join(W, 'material_x2p.pkl'), 'rb'))
    t5 = {int(k): v for k, v in json.load(open(os.path.join(W, '..', 'generic', 'idmap.json')))['5'].items()}
    by_tuple = collections.defaultdict(list)
    for pid, (d, r) in PM.items(): by_tuple[struct.unpack_from('<4I', d, 0x28)].append(pid)
    st = collections.Counter(); fails = []
    for xmid, (xd, xr) in sorted(XM.items()):
        pid = mx2p.get(xmid)
        if pid not in PM: continue
        pd, pr = PM[pid]
        xe = tex_entries(xd, R.parse(xr, 'be'), '>')
        pe = tex_entries(pd, R.parse(pr, 'le'), '<')
        if len(xe) != len(pe): st['skip: entry count differs'] += 1; continue
        flag = lambda d, o: d[o + 12]
        truth = collections.Counter((tid, ty, flag(pd, o), slot) for o, tid, ty, slot in pe)
        if SLOT_ONLY:
            truth = collections.Counter((ty, flag(pd, o), slot) for o, tid, ty, slot in pe)
            mk = lambda slots: collections.Counter((ty, flag(xd, o), s) for (o, tid, ty, _), s in zip(xe, slots))
        else:
            mk = lambda slots: collections.Counter((t5.get(tid, tid), ty, flag(xd, o), s) for (o, tid, ty, _), s in zip(xe, slots))
        if mk([e[3] for e in xe]) == truth: st['0 pairs where copying Xbox slots is already right'] += 1
        else: st['0 pairs where PC moved entries'] += 1
        xt = struct.unpack_from('>4I', xd, 0x28); pt = struct.unpack_from('<4I', pd, 0x28)
        xl = [X.get(s) if s else None for s in xt[:3]]; pl = [P.get(s) if s else None for s in pt[:3]]
        xk = [('x', s) for s in xt[:3]]; pk = [('p', s) for s in pt[:3]]
        moved = mk([e[3] for e in xe]) != truth
        ch = compute_slots(xd, xr, xl, pl, None, xk, pk, fallback=FALLBACK)
        ok = mk([c[3] for c in ch]) == truth
        st['a materials'] += 1; st['a exact'] += ok
        if moved: st['a materials PC moved'] += 1; st['a exact where PC moved'] += ok
        if not ok: fails.append(('a', xmid, pid))
        others = [q for q in by_tuple[pt] if q != pid]
        if others:
            ch2 = compute_slots(xd, xr, xl, pl, PM[others[0]], xk, pk, use_names=False, fallback=FALLBACK)
            ok2 = mk([c[3] for c in ch2]) == truth
            st['b materials (type-only, other ref)'] += 1; st['b exact'] += ok2
            st['b baseline exact (Xbox slots)'] += mk([e[3] for e in xe]) == truth
            if moved: st['b materials PC moved'] += 1; st['b exact where PC moved'] += ok2
    for k, v in sorted(st.items()): print('  %-48s %d' % (k, v))
    print('  first failures', fails[:12])
    return st

def survey(xmids=None):
    """DLC converted materials: entries on a register with another PC sampler name, before/after; DXN normal maps on
    non-Normal samplers before/after (needs texture formats -> only counted via entry type 3)."""
    L = libs(); P, DM = L['P'], L['DM']
    mats, msh, mx2p = dlc_tables()
    st = collections.Counter()
    for xmid, m in sorted(mats.items()):
        if m['source'] != 'converted' or (xmids and xmid not in xmids): continue
        pd, pr = m['data'], m['reloc']
        nd, ch = dlc_reslot(xmid, pd, pr)
        pt = struct.unpack_from('<4I', pd, 0x28)
        pl = [P.get(s) if s else None for s in pt[:3]]; pk = [('p', s) for s in pt[:3]]
        for tag, dd in (('before', pd), ('after', nd)):
            br = bound_report(dd, pr, pl, pk)
            bad3 = sum(1 for r, ns, ty in br if ty == 3 and not any('Normal' in n for n in ns))
            badn = sum(1 for r, ns, ty in br if ty is not None and ty != 3 and all('Normal' in n for n in ns - ENGINE))
            unb = sum(1 for r, ns, ty in br if ty is None)
            st[tag + ': normal map (type 3) on colour sampler'] += bad3
            st[tag + ': colour entry on Normal sampler'] += badn
            st[tag + ': sampled registers without entry'] += unb
            st[tag + ': materials with type-3-on-colour'] += bad3 > 0
        st['materials'] += 1; st['materials changed'] += nd != pd
        for c in ch: st['how ' + c[4]] += 1
    for k, v in sorted(st.items()): print('  %-55s %d' % (k, v))
    return st

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'validate'
    if '--old' in sys.argv: FALLBACK = False; sys.argv.remove('--old')
    if cmd == 'validate':
        SLOT_ONLY = '--slots' in sys.argv
        validate()
    elif cmd == 'survey':
        survey()
    elif cmd == 'patch':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for src in sys.argv[3:]:
            raw = open(src, 'rb').read()
            new, rep = patch_drm(raw)
            name = os.path.basename(src)
            sub = os.path.basename(os.path.dirname(os.path.abspath(src)))
            if sub in ('streamgroups', 'cinstream'): name = os.path.join(sub, name)   # keep mods\ subdirs
            nm = sum(1 for r in rep if r[1])
            print(name, 'converted materials', len(rep), 'changed', nm)
            for mid, moved, unch in rep:
                if moved: print('   mat', mid, 'moved', [(t, ty, a, b, h) for t, ty, a, b, h in moved])
            if new is not None:
                data = DW.cdrm_encode(new, 'le')
                os.makedirs(os.path.dirname(os.path.join(out, name)), exist_ok=True)
                open(os.path.join(out, name), 'wb').write(data)
                print('   wrote', os.path.join(out, name), hashlib.md5(data).hexdigest())
