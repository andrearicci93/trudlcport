"""Valutazione con TEXEL REALI (colore+alfa) dei materiali acqua/cascata: traduzione Xbox (texture Xbox vergini, params Xbox) contro
(a) lib surrogata PC attuale (B87, texture PC, params PC del materiale) e (b) lib nuova (out_unlit). Tutti i sampler reali: nessun grigio di ripiego
tranne gli entry render-target (type 0 flag 9/10 = BackBuffer/Depth, non sono texture).
Uso: unlit_eval.py [MAT ...]"""
import sys, os, io, contextlib, json, struct, pickle
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
texlib.set_baseline('B87_materiali19')
F9, F10, F14, C = B.F9 if hasattr(B, 'F9') else None, None, B.F14, B.F14.C
F9 = B.F14.F9; F10 = B.F14.F10; sm3asm = B.sm3asm
ROOT = B.ROOT
OUT = ROOT + '/work/ws/giro5/out_unlit'
RT_SPECIAL = {9, 10}


def texmap(rows, by_pc):
    m = {}
    for r in rows:
        if r['flag'] in RT_SPECIAL and r['type'] == 0: v = np.array([.5, .5, .5, 1.])
        elif by_pc:
            t = texlib.pc_texel(r['pc_tex']); v = np.array([.5, .5, .5, 1.]) if t is None else t
        else:
            t = texlib.xb_texel(r['xbox_tex']); v = np.array([.5, .5, .5, 1.]) if t is None else t
        m[r['pc_slot'] if by_pc else r['xbox_reg']] = v
    return m


def const_tex(byreg):
    def f(smp, coords, mode):
        v = byreg.get(smp, np.array([.5, .5, .5, 1.]))
        return np.tile(np.asarray(v, np.float32), (coords.shape[0], 1))
    return f


def run(prog, matp, texbyreg, seed=11):
    env = F9.Env(seed, matp); env.tex = const_tex(texbyreg)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), {})
    c = st.get((sm3asm.RT_COLOROUT, 0))
    return None if c is None else c[~kill] if kill is not None and (~kill).any() else c


def mm(c): return None if c is None or len(c) == 0 else np.round(c.mean(0), 3)


def main():
    build = json.load(open(OUT + '/build.json'))['materiali']
    L = B.libs(); D, DM, P = L['D'], L['DM'], L['P']
    t_new = C.read_tree(OUT + '/mods') if os.path.isdir(OUT + '/mods') else None
    t87 = C.read_tree(ROOT + '/work/baseline/B87_materiali19/mods')
    want = {int(a) for a in sys.argv[1:]}
    lines = []
    cov = [0, 0]
    for mid, v in sorted(build.items(), key=lambda kv: int(kv[0])):
        mid = int(mid)
        if want and mid not in want: continue
        if v['status'] != 'costruito': lines.append('mat %d: %s' % (mid, v)); continue
        rel = v['drms'][0]; rows = v['sampler_map']
        for r in rows:
            cov[1] += 1
            cov[0] += (texlib.pc_texel(r['pc_tex']) is not None) and (texlib.xb_texel(r['xbox_tex']) is not None)
        ms = {(s.type, s.id): s for s in t87[rel].sections}[(10, mid)]
        XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(ms, 'le')
        xmap = texmap(rows, False); pmap = texmap(rows, True)
        dl = v['xlib']; old = v['old']
        fn = {(s.type, s.id): s for s in t_new[rel].sections}[(9, v['lib'])]
        fnew = C.frame_lib(fn.data); fold = C.frame_lib({(s.type, s.id): s for s in t87[rel].sections}[(9, old)].data)
        lines.append('\n=== materiale %d (lib Xbox %d, vecchio PC %d -> nuovo %d)  entry: %s' % (mid, dl, old, v['lib'],
                     [(r['type'], r['flag'], r['xbox_tex'], r['pc_tex']) for r in rows]))
        for k in v['occs']:
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            # traduzione Xbox con i registri Xbox come sampler (riferimento)
            pct = []; K = F9.Consts(pct); o = dict(B.material_opts(mid));
            t = B.xenos2sm3.translate(xblob, K.fn, bools=None, samp=lambda n, c: c, opts=o); progX = sm3asm.parse_text(t.text)
            cx = run(progX, XPm, xmap)
            cn = run(sm3asm.decode(fnew['entries'][fnew['slots'][k]]['bc']), PPm, pmap)
            co = run(sm3asm.decode(fold['entries'][fold['slots'][k]]['bc']), PPm, pmap) if fold['slots'][k] != 0xFFFFFFFF else None
            lines.append('  variante %d: RGBA medio  Xbox=%s  NUOVA=%s  VECCHIO(surrogato)=%s' % (k, mm(cx), mm(cn), mm(co)))
    lines.append('\nCOPERTURA texel reali: %d/%d sampler (entry render-target inclusi come grigio)' % tuple(cov))
    open(ROOT + '/work/ws/giro5/unlit_eval.txt', 'w').write('\n'.join(lines)); print('\n'.join(lines))


if __name__ == '__main__':
    main()
