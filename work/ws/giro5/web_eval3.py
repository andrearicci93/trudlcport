"""Ragnatele, valutazione per-texel ALLA PARI (luci accese su entrambi i lati: PC con ALLB, Xbox con xbools) + sensibilita' del surrogato 242 a:
 slot1 (texture 255 bianca vs nera), esponente c104.w (PC 5 vs Xbox 10), colore speculare c101 (PC = Xbox p0.rgb vs 0)."""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F9, B, C, texlib, sm3asm, L, tree = W.F9, W.B, W.C, W.texlib, W.sm3asm, W.L, W.tree
D, DM = L['D'], L['DM']; F10 = W.F10

def run(prog, matp, tex, bools, seed=11, N=4096):
    env = F9.Env(seed, matp, N=N); env.tex = tex
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), bools)
    c = st.get((W.sm3asm.RT_COLOROUT, 0))
    return None if c is None else c[~kill] if kill is not None and (~kill).any() else c

def main(rel, mid):
    s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
    pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
    xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
    xrows = {e['slot']: (e['tex'], True) for e in xe}; prow = {e['slot']: (e['tex'], False) for e in pe}
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
    fn = C.frame_lib({(x.type, x.id): x for x in tree[rel].sections}[(9, pl[2])].data)
    print('== materiale', mid)
    for k in (0,):
        xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][k]]['blob']
        o = dict(B.material_opts(mid))
        px = F9.translate_x(xblob, F9.Consts([]).fn, lambda n, c: c, F9.xbools(xblob), opts=o)[0]
        print('  Xbox (luci accese): ', W.summ(run(px, XPm, W.mk_tex(xrows), None)))
        prog = sm3asm.decode(fn['entries'][fn['slots'][k]]['bc'])
        print('  PC 242 base (ALLB): ', W.summ(run(prog, PPm, W.mk_tex(prow), F9.ALLB)))
        # slot 1 nero
        p2 = dict(prow); base_tex = W.mk_tex(prow)
        def tex_black(smp, coords, mode):
            if smp == 1: return np.tile(np.array([0, 0, 0, 1], np.float32), (coords.shape[0], 1))
            return base_tex(smp, coords, mode)
        print('  PC 242 slot1 NERO:  ', W.summ(run(prog, PPm, tex_black, F9.ALLB)))
        m = [v.copy() for v in PPm]; m[4][3] = 10.0
        print('  PC 242 c104.w=10:   ', W.summ(run(prog, m, W.mk_tex(prow), F9.ALLB)))
        m = [v.copy() for v in PPm]; m[1][:3] = 0.0
        print('  PC 242 c101(spec)=0:', W.summ(run(prog, m, W.mk_tex(prow), F9.ALLB)))
        m = [v.copy() for v in PPm]; m[0][:3] *= 0.5
        print('  PC 242 c100(diff)x.5:', W.summ(run(prog, m, W.mk_tex(prow), F9.ALLB)))
if __name__ == '__main__':
    for spec in sys.argv[1:]:
        r, m = spec.split(':'); main(r, int(m))
