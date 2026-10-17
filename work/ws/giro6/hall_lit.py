"""Cantiere 2a: harness unico sui materiali di un DRM (default dlc_caverns_hall.drm) della baseline: per ogni materiale/variante/modo (luci spente,
luci accese) confronta Xbox (traduzione, texture Xbox vergini, params Xbox) con la lib PC della baseline (texture PC, params PC).
Costanti NON MaterialParams acromatiche (stesso valore sulle 4 lane): luci e ambiente non tingono, quindi la crominanza differente viene
da shader/params/texel. Metrica: chroma = R - (G+B)/2 sul colore medio; ranking per chroma_PC - chroma_Xbox.
Uso: hall_lit.py [BASELINE|MODS_DIR] [DRM]   env STRONG=1: luci dirette forti (Sun c208.., ShadowLights c178.., NonShadowLights c193.., AttenuationSampler=1.0)"""
import sys, os, io, contextlib, struct, json
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
BASELINE = sys.argv[1] if len(sys.argv) > 1 else 'B87_materiali19'
DRM = sys.argv[2] if len(sys.argv) > 2 else 'dlc_caverns_hall.drm'
texlib.set_baseline('B88b_acqua')
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
        if isinstance(v, str):      # 'ATT': AttenuationSampler. Lookup di nebbia (coord y = c54.z = SENT) -> 0 (nessuna nebbia); lookup delle luci -> 1.0
            a = np.where(np.abs(coords[:, 1] - SENT) < 1e-4, 0., 1.).astype(np.float32)
            return np.stack([a, a, a, np.ones_like(a)], 1)
        return np.tile(np.asarray(v, np.float32), (coords.shape[0], 1))
    return f


AMB_RED = os.environ.get('AMB') == 'red'
STRONG = os.environ.get('STRONG') == '1'
SEED = int(os.environ.get('SEED', '5'))
SENT = 0.987654
LD = float(os.environ.get('LD', '2.0'))
def strong_lights(env):
    # struct luce (5 registri): position, direction, attParams, spotParams, diffuseColor ; Sun c208.., ShadowLights c178 (3x5), NonShadowLights c193 (3x5)
    c = env.consts
    def S(r, v): c[r] = np.array(v, np.float32)
    S(54, (c[54][0], c[54][1], SENT, c[54][3]))
    for base in [208] + [178 + 5 * i for i in range(3)] + [193 + 5 * i for i in range(3)]:
        S(base + 1, (-.577, -.577, -.577, c[base + 1][3])); S(base + 4, (LD, LD, LD, LD))
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
        if STRONG: strong_lights(env)
    return env


def color(prog, env, tmap, bools):
    env.tex = const_tex(tmap)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), bools)
    c = st.get((sm3asm.RT_COLOROUT, 0))
    if c is None: return None
    return c[~kill] if kill is not None and (~kill).any() else c


def chroma(c): return None if c is None or len(c) == 0 else float((c[:, 0] - (c[:, 1] + c[:, 2]) / 2).mean())
def nchroma(c):
    if c is None or len(c) == 0: return None
    m = c[:, :3].mean(0); return float((m[0] - (m[1] + m[2]) / 2) / max(float(m.mean()), 1e-6))
def rgb(c): return None if c is None or len(c) == 0 else np.round(c[:, :3].mean(0), 3)


def main():
    L = B.libs(); D, DM, P = L['D'], L['DM'], L['P']
    tree = C.read_tree(BASELINE if os.path.isdir(BASELINE) else ROOT + '/work/baseline/%s/mods' % BASELINE)
    out = []; rank = []; frac = []; lastoff = {}; dfrac = []
    seen = set()
    DRMS = [DRM] if DRM != 'ALL' else sorted(tree)
    for DRM_ in DRMS:
      secs = {(s.type, s.id): s for s in tree[DRM_].sections}
      for (t, mid), ms in sorted(secs.items()):
          if t != 10 or mid not in DM: continue
          dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
          pcl = struct.unpack_from('<4I', ms.data, 0x28)[2]
          if (mid, pcl) in seen: continue
          if (9, pcl) not in secs or dl not in D: out.append('mat %d: lib PC %s non nel DRM / lib Xbox %s assente' % (mid, pcl, dl)); continue
          seen.add((mid, pcl))
          try: slotmap, rows = F14.derive_slotmap(mid, dl, ms.data, ms.reloc)
          except Exception as ex: out.append('mat %d: derive_slotmap fallito %r' % (mid, ex)); continue
          XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(ms, 'le')
          xmap = texmap(rows, False); pmap = texmap(rows, True)
          if STRONG:
              pmap[15] = 'ATT'
              for c_ in XL.parse(D[dl]['entries'][D[dl]['slots'][0]]['blob']).ctab:
                  if c_['set'] == 3 and 'Attenuation' in c_['name']: xmap[c_['reg']] = 'ATT'
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
                  envx = make_env(SEED, XPm, True)
                  if STRONG:
                      for j in range(7):
                          r1_ = K.extra.get(('p_Lights', 13 * j + 1)); r3_ = K.extra.get(('p_Lights', 13 * j + 3))
                          if r1_ is not None: envx.consts[r1_] = np.array([-.577, -.577, -.577, envx.consts[r1_][3]], np.float32)
                          if r3_ is not None: envx.consts[r3_] = np.array([LD, LD, LD, LD], np.float32)
                  cx = color(px, envx, xmap, None)
                  cp = color(prog, make_env(SEED, PPm, True), pmap, pb)
                  chx, chp = chroma(cx), chroma(cp)
                  if chx is None or chp is None: out.append('  v%d %s: nessun colore (X=%s PC=%s)' % (k, lab, chx, chp)); continue
                  d = chp - chx
                  nx_, np_ = nchroma(cx), nchroma(cp); dn = np_ - nx_
                  lum = lambda c: float(c[:, :3].mean())
                  if lab == 'spente': lastoff[(mid, k)] = (lum(cx), lum(cp))
                  extra = ''
                  if lab == 'accese' and (mid, k) in lastoff:
                      ox, op = lastoff[(mid, k)]; fx = 1 - ox / max(lum(cx), 1e-6); fp = 1 - op / max(lum(cp), 1e-6)
                      extra = '  diretto%% X=%.0f PC=%.0f' % (100 * fx, 100 * fp); dfrac.append((fx, fp))
                  out.append('  v%d luci %-6s RGB Xbox=%s PC=%s  chroma X=%+.3f PC=%+.3f  delta=%+.3f  chroma/lum X=%+.3f PC=%+.3f d=%+.3f%s' % (k, lab, rgb(cx), rgb(cp), chx, chp, d, nx_, np_, dn, extra))
                  rank.append((dn, mid, k, lab))
                  if lab == 'accese': frac.append((mid, k, cx, cp))
          if miss: out.append('  (texel PC mancanti per xbox_tex %s)' % miss)
    if dfrac:
        import statistics
        out.append('\n##### quota luce diretta (1 - spente/accese): mediana X=%.0f%% PC=%.0f%%; minimo X=%.0f%% PC=%.0f%%; casi con X<50%%: %d/%d' % (100*statistics.median(a for a,b in dfrac), 100*statistics.median(b for a,b in dfrac), 100*min(a for a,b in dfrac), 100*min(b for a,b in dfrac), sum(1 for a,b in dfrac if a<.5), len(dfrac)))
    rank.sort(reverse=True)
    out.append('\n##### RANKING delta chroma PC-Xbox (R-(G+B)/2), piu\' rossi del dovuto in cima')
    for d, mid, k, lab in rank[:40]: out.append('  %+.3f  mat %d var %d luci %s' % (d, mid, k, lab))
    open(ROOT + '/work/ws/giro6/hall_lit_%s%s%s.txt' % (os.path.basename(BASELINE.rstrip('/')) if not os.path.isdir(BASELINE) else 'compose', '_ambred' if AMB_RED else '', '_strong' if STRONG else ''), 'w').write('\n'.join(out)); print('\n'.join(out))


if __name__ == '__main__':
    main()
