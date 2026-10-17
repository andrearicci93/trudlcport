"""Convert all DLC Material sections (type 10) to PC with the DLC shader remap.
 - material id present in the Xbox base (252, byte-identical, verified): use the real PC material (material_x2p);
   material_convert of these is checked against PC as a sanity test.
 - new materials (587): material_convert with per-material PC shader tuple from work/render/dlc_material_shaders.json
   (A/B libs exact, C/D libs via the material-level surrogate), textures: base ids via the generic idmap,
   new DLC texture ids kept (the DRM writer assigns final ids).
   MaterialParams: rule of the Xbox tuple if known (param_rules.pkl, keyed by base Xbox shader ids - DLC B-class ids are
   translated to their identical base id first); for fallback materials the rule of the chosen base material's tuple
   when the Xbox param count matches; otherwise params are copied and padded/truncated to the surrogate's PC count
   (flagged 'unverified').
Output: work/render/dlc_materials_pc.pkl {xbox_mat_id: dict(data, reloc, source, flags)}, work/render/material_dlc.txt
DRM writer hook: material_for_writer(xmid, xd, xr, tex_map) -> (pc_data, pc_reloc). Shader ids are referenced ONLY from
materials in the DLC (survey of all 311 DLC DRMs: 10766 type-9 idrefs, all from type-10 sections), so the per-material
pc_tuple is authoritative; work/render/dlc_shader_map.json is the per-lib summary.
usage: tools/venv/bin/python -I tools/material_dlc.py"""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material_convert as MC
import drm_reloc as R
from shaderlib import constants
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')

def main():
    L = pickle.load(open(os.path.join(W, 'shaderlibs.pkl'), 'rb'))
    X, P, D, XM, PM, DM = L['X'], L['P'], L['D'], L['XM'], L['PM'], L['DM']
    mx2p = pickle.load(open(os.path.join(W, 'material_x2p.pkl'), 'rb'))
    sx2p = pickle.load(open(os.path.join(W, 'shader_x2p.pkl'), 'rb'))
    rules = pickle.load(open(os.path.join(W, 'param_rules.pkl'), 'rb'))
    smap = {int(k): v for k, v in json.load(open(os.path.join(W, 'dlc_shader_map.json'))).items()}
    mshad = {int(k): v for k, v in json.load(open(os.path.join(W, 'dlc_material_shaders.json'))).items()}
    gid = json.load(open(os.path.join(W, '..', 'generic', 'idmap.json')))
    t5 = {int(k): v for k, v in gid['5'].items()}
    st = collections.Counter(); fails = []; out = {}
    base_tuples = {MC.shader_key(d) for d, r in XM.values()}
    def _unused_pc_samplers(pid):
        lib = P.get(pid)
        if lib is None: return None
        regs = set()
        for s in set(lib['slots']) - {0xFFFFFFFF}:
            v, c = constants(lib['entries'][s]['blob'], 'p')
            regs |= {ri for n, rs, ri, rc in c if rs == 3}
        return regs
    for mid, (d, r) in sorted(DM.items()):
        st['n'] += 1
        if mid in XM:
            st['base material'] += 1
            pid = mx2p.get(mid)
            if pid in PM:
                pd, pr = PM[pid]
                t = MC.shader_key(d); rule = rules.get(t)
                cd, cr = MC.convert(d, r, lambda i: sx2p.get(i, i), lambda i: t5.get(i, i), param_rule=(lambda v, rr=rule: MC.apply_rule(rr, v)) if rule else None)
                st['base material: convert == PC'] += cd == pd
                out[mid] = dict(data=pd, reloc=pr, source='PC material %d' % pid, flags=[])
            else:
                st['base material without PC id (FAIL)'] += 1; fails.append((mid, 'base material without PC id'))
            continue
        flags = []
        t = MC.shader_key(d)
        ms = mshad.get(mid)
        if ms is None: fails.append((mid, 'no shader tuple')); st['FAIL no shader tuple'] += 1; continue
        ptup = ms['pc_tuple']
        xm = {}
        for xs, ps in zip(t, ptup):
            if xs == 0: continue
            if ps in (0, None): flags.append('shader %d unmapped' % xs)
            if xs in xm and xm[xs] != ps: flags.append('shader %d used with 2 PC ids' % xs)
            xm[xs] = ps
        if any(f.endswith('unmapped') for f in flags):
            fails.append((mid, flags)); st['FAIL shader unmapped'] += 1; continue
        cls = [smap[s]['cls'] if s in smap else 'base' for s in t if s]
        exact = all(c in ('A', 'B') for c in cls)
        st['new material, all shaders exact (A/B)' if exact else 'new material, surrogate shaders (C/D)'] += 1
        # params
        nx = struct.unpack_from('>I', d, 0x58)[0]
        bt = tuple(smap[s]['surrogate'] if s in smap else s for s in t)   # Xbox base ids (B -> identical base id)
        rule = rules.get(bt) if exact else None
        if exact and bt not in base_tuples: flags.append('tuple unseen in base')
        bm = ms.get('base_material')
        target_n = None
        if rule is None and not exact and bm is not None:
            bd = XM[bm][0]; bnx = struct.unpack_from('>I', bd, 0x58)[0]
            brule = rules.get(MC.shader_key(bd))
            pcn = struct.unpack_from('<I', PM[mx2p[bm]][0], 0x58)[0]
            if nx == bnx:
                rule = brule
                if rule: flags.append('param rule of surrogate base material %d' % bm)
            else:
                target_n = pcn
                flags.append('UNVERIFIED params %d vec4 -> %d (surrogate base material %d)' % (nx, pcn, bm))
        if rule is not None: pr_ = lambda v, rr=rule: MC.apply_rule(rr, v)
        elif target_n is not None: pr_ = lambda v, n=target_n: (list(v) + [(0.0, 0.0, 0.0, 0.0)] * n)[:n]
        else: pr_ = None
        try:
            cd, cr = MC.convert(d, r, lambda i: xm.get(i, i), lambda i: t5.get(i, i), param_rule=pr_)
        except Exception as e:
            fails.append((mid, 'convert exception ' + repr(e)[:120])); st['FAIL exception'] += 1; continue
        rel = R.parse(cr, 'le')
        if R.check(rel, len(cd)): fails.append((mid, 'reloc bounds')); st['FAIL reloc bounds'] += 1; continue
        # texture count vs the surrogate base material (a material-sampler bound by the PC shader may stay unset)
        if not exact and bm is not None:
            ntex = sum(1 for ty, o in R.parse(r, 'be').idref + R.parse(r, 'be').idref_a if ty == 5)
            bnt = sum(1 for ty, o in R.parse(XM[bm][1], 'be').idref + R.parse(XM[bm][1], 'be').idref_a if ty == 5)
            if ntex < bnt: flags.append('PC PS fewer textures (%d) than surrogate base material %d (%d)' % (ntex, bm, bnt))
        for f in flags:
            key = ('UNVERIFIED param count differs from surrogate (copied+padded/truncated)' if f.startswith('UNVERIFIED') else
                   'param rule taken from surrogate base material' if f.startswith('param rule') else
                   'fewer textures than the surrogate base material' if f.startswith('PC PS') else
                   'exact shaders but Xbox tuple unseen in base (params copied 1:1, unverified)' if f.startswith('tuple') else f)
            st['flag: ' + key] += 1
        out[mid] = dict(data=cd, reloc=cr, source='converted', flags=flags, pc_tuple=ptup)
    pickle.dump(out, open(os.path.join(W, 'dlc_materials_pc.pkl'), 'wb'))
    lines = ['DLC materials: %d, converted/resolved: %d, failed: %d' % (st['n'], len(out), len(fails))]
    lines += ['  %-60s %d' % kv for kv in sorted(st.items())]
    lines += ['failures:'] + ['  %r' % (f,) for f in fails]
    txt = '\n'.join(lines); print(txt); open(os.path.join(W, 'material_dlc.txt'), 'w').write(txt + '\n')

_CACHE = None
def material_for_writer(xmid, xd, xr, tex_map):
    """DRM-writer hook: PC (data, reloc_le) for DLC material xmid (Xbox data xd / reloc xr), with texture ids
    remapped by the writer's tex_map(xbox_tex_id) -> pc id (base materials are returned as the real PC material,
    whose texture ids are already PC ids). Uses work/render/dlc_materials_pc.pkl (run main() first)."""
    global _CACHE
    if _CACHE is None: _CACHE = pickle.load(open(os.path.join(W, 'dlc_materials_pc.pkl'), 'rb'))
    m = _CACHE[xmid]
    if m['source'] != 'converted': return m['data'], m['reloc']
    xr_ = R.parse(xr, 'be'); cr = R.parse(m['reloc'], 'le')
    xo = [o for t, o in xr_.idref + xr_.idref_a if t == 5]; co = [o for t, o in cr.idref + cr.idref_a if t == 5]
    assert len(xo) == len(co)
    out = bytearray(m['data'])
    for a, b in zip(xo, co):
        struct.pack_into('<I', out, b, tex_map(struct.unpack_from('>I', xd, a)[0]))
    if PARAM_AUTO:  # MaterialParams re-packing for PROVEN-MAP surrogate pairs only (tools/param_auto.py; today: 21118)
        import param_auto
        nd, info = param_auto.fix_section(xmid, bytes(out), m['reloc'])
        if info is not None: out = bytearray(nd)
    if RESLOT:      # texture SLOT re-binding for surrogate PS libs (tools/material_reslot.py, mods_glitchfix2 rule)
        import material_reslot
        nd, ch = material_reslot.dlc_reslot(xmid, bytes(out), m['reloc'])
        if ch is not None: return nd, m['reloc']
    return bytes(out), m['reloc']
PARAM_AUTO = True    # False = params copied 1:1 (pre-fix17 look of 21118)
RESLOT = True       # False reproduces the pre-glitchfix slots (Xbox slots copied 1:1)

if __name__ == '__main__':
    main()
