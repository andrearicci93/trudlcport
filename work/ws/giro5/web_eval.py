"""Cantiere 3b: cosa calcola il surrogato PC (lib 242, variante pos2) sulle ragnatele rispetto alla traduzione Xbox diretta (lib 2199/2209), texel reali.
Mappa sampler: Xbox slot -> texel Xbox; PC slot -> texel PC (entry t7/f2 tex255 = placeholder bianco 4x4)."""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
texlib.set_baseline('B87_materiali19')
F14 = B.F14; F9 = F14.F9; F10 = F14.F10; C = F14.C; sm3asm = B.sm3asm; XL = B.XL; xenos2sm3 = B.xenos2sm3
L = B.libs(); D, DM, P = L['D'], L['DM'], L['P']
tree = C.read_tree(B.ROOT + '/work/baseline/B87_materiali19/mods')
RT = {9, 10}


def const_tex(byreg, log=None):
    def f(smp, coords, mode):
        v = byreg.get(smp, np.array([.5, .5, .5, 1.]))
        return np.tile(np.asarray(v, np.float32), (coords.shape[0], 1))
    return f


def run(prog, matp, tmap, seed=11):
    env = F9.Env(seed, matp); env.tex = const_tex(tmap)
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), {})
    c = st.get((sm3asm.RT_COLOROUT, 0))
    return None if c is None else c[~kill] if kill is not None and (~kill).any() else c


def main(rel, mid):
    s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
    pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
    xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
    xmap = {}; pmap = {}
    for e in xe:
        t = texlib.xb_texel(e['tex']); xmap[e['slot']] = np.array([.5] * 3 + [1.]) if t is None else t
    for e in pe:
        t = texlib.pc_texel(e['tex']); pmap[e['slot']] = np.array([.5] * 3 + [1.]) if t is None else t
    print('materiale', mid, rel, 'Xlib', xl, 'PClib', pl)
    print('  Xbox tex medi:', {e['slot']: (e['tex'], np.round(xmap[e['slot']], 3).tolist()) for e in xe})
    print('  PC   tex medi:', {e['slot']: (e['tex'], np.round(pmap[e['slot']], 3).tolist()) for e in pe})
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(s, 'le')
    print('  params Xbox', [np.round(v, 3).tolist() for v in XPm][:8]); print('  params PC  ', [np.round(v, 3).tolist() for v in PPm][:8])
    fn = C.frame_lib({(x.type, x.id): x for x in tree[rel].sections}[(9, pl[2])].data) if (9, pl[2]) in {(x.type, x.id) for x in tree[rel].sections} else None
    for k in (0, 1):
        xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][k]]['blob']
        K = F9.Consts([]); o = dict(B.material_opts(mid))
        px = F9.translate_x(xblob, K.fn, lambda n, c: c, F9.xbools(xblob), opts=o)[0]
        cx = run(px, XPm, xmap)
        res = 'Xbox=%s' % (None if cx is None else np.round(cx.mean(0), 3))
        if fn is not None:
            for kk in range(len(fn['slots'])):
                if kk & 1 != k or fn['slots'][kk] == 0xFFFFFFFF: continue
                cp = run(sm3asm.decode(fn['entries'][fn['slots'][kk]]['bc']), PPm, pmap)
                res += '  PC(var%d)=%s' % (kk, None if cp is None else np.round(cp.mean(0), 3))
        print('  variante Xbox %d:' % k, res)
    return


if __name__ == '__main__':
    for spec in sys.argv[1:]:
        r, m = spec.split(':'); main(r, int(m))
