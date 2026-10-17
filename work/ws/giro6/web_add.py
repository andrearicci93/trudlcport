"""Giro 6: ragnatele con blend ADDITIVO reale (mat+0x38=5 -> SRCALPHA,ONE, FUN_00527a80) e c98.x=MaterialOpacity=1 (non random).
Contributo additivo = rgb*alfa dell'uscita PS (var0), per-texel su immagini reali, Xbox (texture Xbox vergini) vs PC (compose)."""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0,'/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F9, B, C, sm3asm, L, F10 = W.F9, W.B, W.C, W.sm3asm, W.L, W.F10
D, DM = L['D'], L['DM']
tree = C.read_tree('/path/to/trudlcport/work/ws/giro6/compose/mods')
def run(prog, matp, tex, bools, c98=1.0, seed=11, N=4096):
    env = F9.Env(seed, matp, N=N); env.tex = tex; env.consts[98] = np.array([c98]*4, np.float32)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), bools)
    c = st.get((sm3asm.RT_COLOROUT, 0)); return c
def main(rel, mid):
    s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
    pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
    xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
    xrows = {e['slot']: (e['tex'], True) for e in xe}; prow = {e['slot']: (e['tex'], False) for e in pe}
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
    fn = C.frame_lib({(x.type, x.id): x for x in tree[rel].sections}[(9, pl[2])].data)
    xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][0]]['blob']
    o = dict(B.material_opts(mid))
    px = F9.translate_x(xblob, F9.Consts([]).fn, lambda n, c: c, F9.xbools(xblob), opts=o)[0]
    cx = run(px, XPm, W.mk_tex(xrows), None)
    cp = run(sm3asm.decode(fn['entries'][fn['slots'][0]]['bc']), PPm, W.mk_tex(prow), F9.ALLB)
    ax = cx[:, :3] * np.clip(cx[:, 3:4], 0, 1); ap = cp[:, :3] * np.clip(cp[:, 3:4], 0, 1)
    lx, lp = ax.mean(1), ap.mean(1)
    print('mat %d  alfa Xbox p50/p90=%s  PC p50/p90=%s | additivo medio rgb*a: Xbox=%s PC=%s  rapporto PC/Xbox=%.3f | lum p90 Xbox=%.3f PC=%.3f | frazione lum>0.5: Xbox %.3f PC %.3f' % (
        mid, np.round(np.percentile(cx[:, 3], [50, 90]), 3), np.round(np.percentile(cp[:, 3], [50, 90]), 3), np.round(ax.mean(0), 3), np.round(ap.mean(0), 3),
        lp.mean() / max(lx.mean(), 1e-9), np.percentile(lx, 90), np.percentile(lp, 90), (lx > .5).mean(), (lp > .5).mean()))
for spec in sys.argv[1:]:
    r, m = spec.split(':'); main(r, int(m))
