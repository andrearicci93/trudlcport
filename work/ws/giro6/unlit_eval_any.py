"""Giro 6 task 4: valutazione con texel reali dei materiali NON illuminati gia' presenti nella baseline (qualsiasi lib PC attuale in pos2):
Xbox (traduzione, texel Xbox vergini, params Xbox) vs PC attuale (lib in pos2 del DRM, texel PC, params PC). Uso: unlit_eval_any.py MODS_DIR MAT ...  (MAT=all -> tutti i candidati del censimento)"""
import sys, os, io, contextlib, json, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5'); sys.path.insert(0, '/path/to/trudlcport/work/ws/giro6')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import unlit_eval as E
import texlib
texlib.set_baseline('B88b_acqua')
F9, F10, F14, C, sm3asm = E.F9, E.F10, E.F14, E.C, E.sm3asm
mods = sys.argv[1]; want = [int(x) for x in sys.argv[2:] if x != 'all']
L = B.libs(); D, DM = L['D'], L['DM']
tree = C.read_tree(mods)
occ = {}
for rel, d in tree.items():
    for s in d.sections:
        if s.type == 10 and s.id in DM: occ.setdefault(s.id, []).append((rel, s))
res = []
for mid in (want or sorted(occ)):
    if mid not in occ: print(mid, 'non nei DRM'); continue
    rel, s = occ[mid][0]
    dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]; pc = struct.unpack_from('<4I', s.data, 0x28)[2]
    if dl in (0, 0xffffffff) or dl not in D or D[dl].get('kind') != 1: continue
    names = set()
    for sl in set(D[dl]['slots']) - {0xFFFFFFFF}: names |= {c['name'] for c in B.XL.parse(D[dl]['entries'][sl]['blob']).ctab}
    if any(('p_Lights' in n or 'ShadowMap' in n or 'LightEnabled' in n or 'Irradiance' in n or 'ModulationMaps' in n or 'ParallelShadow' in n) for n in names): continue
    slotmap, rows = F14.derive_slotmap(mid, dl, s.data, s.reloc)
    lib = {x.id: x for x in tree[rel].sections if x.type == 9}.get(pc)
    if lib is None: print(mid, 'lib PC', pc, 'non nel DRM', rel); continue
    fl = C.frame_lib(lib.data)
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(s, 'le')
    xmap = E.texmap(rows, False); pmap = E.texmap(rows, True)
    mo = dict(B.material_opts(mid))
    dxn = {r['xbox_reg'] for r in rows if (texlib.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN'}
    if dxn: mo['dxn'] = dxn
    out = []
    for k in range(2):
        if fl['slots'][k] == 0xFFFFFFFF: continue
        xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
        try:
            t = B.xenos2sm3.translate(xblob, F9.Consts([]).fn, bools=None, samp=lambda n, c: c, opts=dict(B.material_opts(mid))); progX = sm3asm.parse_text(t.text)
            cx = E.mm(E.run(progX, XPm, xmap)); cp = E.mm(E.run(sm3asm.decode(fl['entries'][fl['slots'][k]]['bc']), PPm, pmap))
        except Exception as ex:
            out.append((k, 'ERR %r' % (ex,)[:80])); continue
        out.append((k, None if cx is None else cx.tolist(), None if cp is None else cp.tolist()))
    flag = ''
    for o in out:
        if len(o) == 3 and o[1] is not None and o[2] is not None:
            dmax = max(abs(a - b) for a, b in zip(o[1], o[2]))
            if dmax > 0.05: flag = ' <== DIFF %.3f' % dmax
    ok = 'OK ' if not flag else 'DIFF'
    print('%s mat %d lib Xbox %d PC %d dxn %s %s' % (ok, mid, dl, pc, sorted(dxn), [(o[0], [round(v, 3) for v in o[1]] if len(o) == 3 and o[1] else o[1:], [round(v, 3) for v in o[2]] if len(o) == 3 and o[2] else None) for o in out]) + flag, flush=True)
