"""Gate offline con TEXEL REALI per i 19 materiali di B87 (luci spente): traduzione Xbox vs (a) lib surrogata PC di B86 (stato attuale) e (b) lib nuova di B87.
Stessa funzione di real_tex_gate.py (riusa pc_mean/xbox_texel/pc_texel/colors); copertura: quanti sampler hanno texel reale (non grigio di ripiego).
Uso: tools/venv/bin/python -I work/ws/codefirst/real_tex_gate_B87.py"""
import sys, os, json, io, contextlib, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
import numpy as np
F, C, H, F12, F10, sm3asm, libs = G.F, G.C, G.H, G.F12, G.F10, G.sm3asm, G.libs
T = '/path/to/trudlcport/'
t86 = C.read_tree(T + 'work/baseline/B86_contratti/mods'); t87 = C.read_tree(T + 'work/baseline/B87_materiali19/mods')
bj = json.load(open(T + 'work/ws/codefirst/out_B87/B87_build.json'))['materiali']
lines = []; tot = dict(var=0, ok_new=0, worse=0); cov = [0, 0]
for mid, v in sorted(bj.items(), key=lambda kv: int(kv[0])):
    mid = int(mid); rel = v['drms'][0]
    secs = {(s.type, s.id): s for s in t87[rel].sections}; ms = secs[(10, mid)]
    slotmap, rows = F.derive_slotmap(mid, struct.unpack_from('>4I', libs()['DM'][mid][0], 0x28)[2], ms.data, ms.reloc)
    dl = struct.unpack_from('>4I', libs()['DM'][mid][0], 0x28)[2]
    mo = F12.material_opts(mid); XPm = F10.params(F10.f9_common._Sec(*libs()['DM'][mid]), 'be')
    xmap = {r['xbox_reg']: G.xbox_texel(r) for r in rows}; pmap = {r['pc_slot']: G.pc_texel(r) for r in rows}
    for r in rows:
        cov[1] += 1; cov[0] += G.pc_mean(r['pc_tex']) is not None and G.pc_mean(r['pc_tex'])[0] != 'cube'
    old = G.lib_bcs(t86, rel, v['old']); new = G.lib_bcs(t87, rel, v['lib'])
    D = libs()['D']; lines.append('\n=== materiale %d: lib surrogata %d -> lib nuova %d (%s)' % (mid, v['old'], v['lib'], rel))
    for k in sorted(new):
        xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
        res = {}
        for name, bcs in (('B86', old), ('B87', new)):
            if k not in bcs: res[name] = None; continue
            ca, cb = G.colors(sm3asm.decode(bcs[k]), xblob, XPm, mo, xmap, pmap); res[name] = ca; res['X'] = cb
        X = res['X']
        def err(c): return None if c is None or X is None else round(float(np.abs(c[:, :3] - X[:, :3]).mean()), 4)
        e86, e87 = err(res['B86']), err(res['B87'])
        tot['var'] += 1; tot['ok_new'] += (e87 is not None and e87 < 0.02); tot['worse'] += (e87 is not None and e86 is not None and e87 > e86 + 1e-4)
        lines.append('  variante %d: |err| vs Xbox  B86(surrogato)=%s  B87(nuova)=%s' % (k, e86, e87))
lines.append('\nRIEPILOGO: varianti %(var)d, |err| B87 < 0.02: %(ok_new)d, varianti dove B87 e\' peggio di B86: %(worse)d; sampler con texel reale %%d/%%d' % tot % tuple(cov))
open(T + 'work/ws/codefirst/gates_B87/real_tex_gate_B87.txt', 'w').write('\n'.join(lines)); print('\n'.join(lines))
