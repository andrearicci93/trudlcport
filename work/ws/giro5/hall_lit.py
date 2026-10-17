"""Cantiere 2a: harness unico sui materiali di un DRM (default dlc_caverns_hall.drm) della baseline: per ogni materiale/variante/modo (luci spente,
luci accese) confronta Xbox (traduzione, texture Xbox vergini, params Xbox) con la lib PC della baseline (texture PC, params PC).
Costanti NON MaterialParams acromatiche (stesso valore sulle 4 lane): luci e ambiente non tingono, quindi la crominanza differente viene
da shader/params/texel. Metrica: chroma = R - (G+B)/2 sul colore medio; ranking per chroma_PC - chroma_Xbox.
Uso: hall_lit.py [BASELINE] [DRM]"""
import sys, os, io, contextlib, struct, json
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
BASELINE = sys.argv[1] if len(sys.argv) > 1 else 'B87_materiali19'
DRM = sys.argv[2] if len(sys.argv) > 2 else 'dlc_caverns_hall.drm'
texlib.set_baseline(BASELINE)
F14 = B.F14; F9 = F14.F9; F10 = F14.F10; C = F14.C; sm3asm = B.sm3asm; XL = B.XL; xenos2sm3 = B.xenos2sm3
ROOT = B.ROOT
RT = {9, 10}


def texmap(rows, by_pc):
    m = {}
    for r in rows:
        if r['flag'] in RT and r['type'] == 0: v = np.array([.5, .5, .5, 1.])
        else:
            t = texlib.pc_texel(r['pc_tex']) if by_pc else texlib.xb_texel(r['xbox_tex'])
            v = np.array([np.nan] * 4) if t is None else t
        m[r['pc_slot'] if by_pc else r['xbox_reg']] = v
    return m


def const_tex(byreg):
    def f(smp, coords, mode):
        v = byreg.get(smp, np.array([.5, .5, .5, 1.]))
        return np.tile(np.asarray(v, np.float32), (coords.shape[0], 1))
    return f


AMB_RED = os.environ.get('AMB') == 'red'
# ambiente PC (g_Ambient c15, IrradianceState Red0/1 c70/71, Green c72/73, Blue c74/75, Base c76): con AMB=red canale R forte, G/B deboli
AMB = {15: (.5, .1, .1, 1.), 70: (.5,) * 4, 71: (.5,) * 4, 72: (.1,) * 4, 73: (.1,) * 4, 74: (.1,) * 4, 75: (.1,) * 4, 76: (.5, .1, .1, 0.)}


def make_env(seed, matp, achrom):
    env = F9.Env(seed, matp)
    if achrom:
        keep = set(range(100, 100 + len(matp)))
        for r in list(env.consts):
            if r not in keep: env.consts[r] = np.full(4, env.consts[r][0], np.float32)
        if AMB_RED:
            for r, v in AMB.items(): env.consts[r] = np.array(v, np.float32)
    return env


def color(prog, env, tmap, bools):
    env.tex = const_tex(tmap)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), bools)
    c = st.get((sm3asm.RT_COLOROUT, 0))
    if c is None: return None
    return c[~kill] if kill is not None and (~kill).any() else c


def chroma(c): return None if c is None or len(c) == 0 else float((c[:, 0] - (c[:, 1] + c[:, 2]) / 2).mean())
def rgb(c): return None if c is None or len(c) == 0 else np.round(c[:, :3].mean(0), 3)


def main():
    L = B.libs(); D, DM, P = L['D'], L['DM'], L['P']
    tree = C.read_tree(ROOT + '/work/baseline/%s/mods' % BASELINE)
    secs = {(s.type, s.id): s for s in tree[DRM].sections}
    out = []; rank = []
    for (t, mid), ms in sorted(secs.items()):
        if t != 10 or mid not in DM: continue
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        pcl = struct.unpack_from('<4I', ms.data, 0x28)[2]
        if (9, pcl) not in secs or dl not in D: out.append('mat %d: lib PC %s non nel DRM / lib Xbox %s assente' % (mid, pcl, dl)); continue
        try: slotmap, rows = F14.derive_slotmap(mid, dl, ms.data, ms.reloc)
        except Exception as ex: out.append('mat %d: derive_slotmap fallito %r' % (mid, ex)); continue
        XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(ms, 'le')
        xmap = texmap(rows, False); pmap = texmap(rows, True)
        miss = [r['xbox_tex'] for r in rows if r['pc_tex'] is not None and np.isnan(pmap.get(r['pc_slot'], np.zeros(4))).any()]
        fl = C.frame_lib(secs[(9, pcl)].data)
        mo = B.material_opts(mid)
        dxn_x = {r['xbox_reg'] for r in rows if (texlib.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN'}
        out.append('\n=== materiale %d (lib Xbox %d, lib PC %d)  sampler: %s' % (mid, dl, pcl,
                   ['%s%s' % ((texlib.xb_mean(r['xbox_tex']) or {}).get('kind', '?'), '/cubo' if (texlib.xb_mean(r['xbox_tex']) or {}).get('cube') else '') for r in rows]))
        worst = None
        for k, off in enumerate(fl['slots']):
            if off == 0xFFFFFFFF or k > 1 and False: continue
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            prog = sm3asm.decode(fl['entries'][off]['bc'])
            for lab, xb, pb in (('spente', 'off', {}), ('accese', 'on', F9.ALLB)):
                pct = []; K = F9.Consts(pct); sh = XL.parse(xblob); bn = F9.bool_names(sh)
                bools = {i: 0 for i in bn} if xb == 'off' else F9.xbools(xblob) and {i: (0 if n == 'p_ShadowEnabled' else 1) for i, n in bn.items()}
                o = dict(mo); o['noopt'] = True
                try:
                    tx = xenos2sm3.translate(xblob, K.fn, bools=bools, samp=lambda n, c: c, opts=o); px = sm3asm.parse_text(tx.text)
                except Exception as ex: out.append('  v%d %s: traduzione Xbox fallita %r' % (k, lab, ex)); continue
                cx = color(px, make_env(5, XPm, True), xmap, None)
                cp = color(prog, make_env(5, PPm, True), pmap, pb)
                chx, chp = chroma(cx), chroma(cp)
                if chx is None or chp is None: out.append('  v%d %s: nessun colore (X=%s PC=%s)' % (k, lab, chx, chp)); continue
                d = chp - chx
                out.append('  v%d luci %-6s RGB Xbox=%s PC=%s  chroma X=%+.3f PC=%+.3f  delta=%+.3f' % (k, lab, rgb(cx), rgb(cp), chx, chp, d))
                rank.append((d, mid, k, lab))
        if miss: out.append('  (texel PC mancanti per xbox_tex %s)' % miss)
    rank.sort(reverse=True)
    out.append('\n##### RANKING delta chroma PC-Xbox (R-(G+B)/2), piu\' rossi del dovuto in cima')
    for d, mid, k, lab in rank[:40]: out.append('  %+.3f  mat %d var %d luci %s' % (d, mid, k, lab))
    open(ROOT + '/work/ws/giro5/hall_lit_%s%s.txt' % (BASELINE, '_ambred' if AMB_RED else ''), 'w').write('\n'.join(out)); print('\n'.join(out))


if __name__ == '__main__':
    main()
