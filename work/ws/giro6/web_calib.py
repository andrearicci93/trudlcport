"""Giro 7 punto 2: calibrazione K per ragnatele (additive, +0x38=5). K = media(RGB*alfa) su pixel-maglia (tex 6610 lum>0.25) Xbox / PC(K=1),
con ambiente forte + luce diretta forte identici su entrambi i lati (hall_lit.strong_lights), c98.x=1, nebbia azzerata.
Uso: web_calib.py [BASE_MODS]  (default B88b_acqua: c104.x=1 originale)"""
import sys, io, contextlib, struct, os
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F9, B, C, sm3asm, L, F10, XL = W.F9, W.B, W.C, W.sm3asm, W.L, W.F10, W.XL
D, DM = L['D'], L['DM']
BASE = sys.argv[1] if len(sys.argv) > 1 else '/path/to/trudlcport/work/baseline/B88b_acqua/mods'
tree = C.read_tree(BASE)
WEBS = [23173, 23329, 20673, 20676, 20876]
STRAND = [None]
SENT = 0.987654

def find(mid):
    for rel, d in sorted(tree.items()):
        for s in d.sections:
            if s.type == 10 and s.id == mid: return rel, {(x.type, x.id): x for x in d.sections}
    return None, None

def env_for(seed, matp, amb, ld, K=None, xbox=False):
    env = F9.Env(seed, matp, N=8192)
    keep = set(range(100, 100 + len(matp)))
    for r in list(env.consts):
        if r not in keep: env.consts[r] = np.full(4, env.consts[r][0], np.float32)
    S = lambda r, v: env.consts.__setitem__(r, np.array(v, np.float32))
    for r in (15, 70, 71, 72, 73, 74, 75, 76): S(r, (amb,) * 4)
    S(98, (1.0,) * 4)
    S(54, (env.consts[54][0], env.consts[54][1], SENT, env.consts[54][3]))
    for base in [208] + [178 + 5 * i for i in range(3)] + [193 + 5 * i for i in range(3)]:
        S(base + 1, (-.577, -.577, -.577, env.consts[base + 1][3])); S(base + 4, (ld,) * 4)
    if xbox and K is not None:
        for j in range(7):
            r1 = K.extra.get(('p_Lights', 13 * j + 1)); r3 = K.extra.get(('p_Lights', 13 * j + 3))
            if r1 is not None: S(r1, (-.577, -.577, -.577, env.consts[r1][3]))
            if r3 is not None: S(r3, (ld,) * 4)
        for (n, j), r in K.extra.items():
            if 'Fog' in n: S(r, (0,) * 4)
    return env

def tex_fn(rows, rec, att_regs):
    base = W.mk_tex(rows)
    def f(smp, coords, mode):
        if smp in att_regs:      # s15: lookup di NEBBIA (v = c54.z = SENT) -> 0 (nessuna nebbia); lookup attenuazione luci -> 1 (come hall_lit 'ATT')
            a = np.where(np.abs(coords[:, 1] - SENT) < 1e-4, 0., 1.).astype(np.float32)
            return np.stack([a, a, a, np.ones_like(a)], 1)
        v = base(smp, coords, mode)
        if rows.get(smp, (None,))[0] == STRAND[0] and 'm' not in rec: rec['m'] = v[:, :3].mean(1).copy()
        return v
    return f

def runp(prog, env, rows, bools, att):
    rec = {}
    env.tex = tex_fn(rows, rec, att)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), bools)
    c = st.get((sm3asm.RT_COLOROUT, 0))
    return c, rec.get('m'), kill

def main():
    res = {}
    for mid in WEBS:
        rel, secs = find(mid)
        s = secs[(10, mid)]
        pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
        xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
        xrows = {e['slot']: (e['tex'], True) for e in xe}; prow = {e['slot']: (e['tex'], False) for e in pe}
        XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
        fn = C.frame_lib(secs[(9, pl[2])].data)
        print('== mat %d (%s)  libX %d  libPC %d  tex Xbox %s  PC %s' % (mid, rel.split('/')[-1], xl[2], pl[2], sorted(xrows.items()), sorted(prow.items())), flush=True)
        print('   c104.x PC=%s  c105 PC=%s | Xbox p0=%s p1=%s' % (PPm[4][0], PPm[5], np.round(XPm[0], 3), np.round(XPm[1], 3)))
        STRAND[0] = prow[3][0]
        for var in (0, 1):
            pprog = sm3asm.decode(fn['entries'][fn['slots'][var]]['bc'])
            xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][var]]['blob']
            Kc = F9.Consts([]); o = dict(B.material_opts(mid))
            px = F9.translate_x(xblob, Kc.fn, lambda n, c: c, F9.xbools(xblob), opts=o)[0]
            xatt = {c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 3 and 'Attenuation' in c['name']}
            for amb, ld in ((1.0, 2.0), (1.0, 0.0), (0.3, 2.0)):
                ex = env_for(11, XPm, amb, ld, Kc, True); ep = env_for(11, PPm, amb, ld)
                cx, mx, kx = runp(px, ex, xrows, None, xatt)
                cp, mp, kp = runp(pprog, ep, prow, F9.ALLB, {15})
                if mx is None or mp is None: print('   var%d: nessun campione maglia (X=%s PC=%s)' % (var, mx is None, mp is None)); continue
                m = mp > 0.25
                ax = cx[:, :3] * np.clip(cx[:, 3:4], 0, 1); ap = cp[:, :3] * np.clip(cp[:, 3:4], 0, 1)
                kk = np.zeros(len(m), bool) if kx is None else kx
                mm = m & ~kk
                if mm.sum() < 20: print('   var%d amb %.1f ld %.1f: troppo pochi pixel-maglia (%d)' % (var, amb, ld, mm.sum())); continue
                xm, pm = ax[mm].mean(0), ap[mm].mean(0)
                ratio = xm / np.maximum(pm, 1e-9)
                print('   var%d amb %.1f ld %.1f  n=%d  alfaX=%.3f alfaPC=%.3f  RGB*a Xbox=%s PC=%s  K(rgb)=%s  K=%.3f' % (
                    var, amb, ld, mm.sum(), cx[mm, 3].mean(), cp[mm, 3].mean(), np.round(xm, 3), np.round(pm, 3), np.round(ratio, 3), ratio.mean()), flush=True)
                res[(mid, var, amb, ld)] = ratio.mean()
    print('\nRIEPILOGO K (amb 1.0, ld 2.0):')
    for mid in WEBS: print('  %d: var0=%s var1=%s' % (mid, res.get((mid, 0, 1.0, 2.0)), res.get((mid, 1, 1.0, 2.0))))

main()
