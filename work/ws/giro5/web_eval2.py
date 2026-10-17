"""Cantiere 3b: valutazione PER-TEXEL (immagini reali 2D, campionamento nearest su UV casuali condivise) del surrogato 242 contro la traduzione Xbox diretta.
Distribuzioni di RGB e alfa (percentili), frazione di campioni 'bianchi' (lum>0.7) e frazione di pixel con alfa utile. Cubi/non-2D: media costante."""
import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
texlib.set_baseline('B87_materiali19')
TC = texlib.TC
F14 = B.F14; F9 = F14.F9; F10 = F14.F10; C = F14.C; sm3asm = B.sm3asm; XL = B.XL; xenos2sm3 = B.xenos2sm3
L = B.libs(); D, DM, P = L['D'], L['DM'], L['P']
tree = C.read_tree(B.ROOT + '/work/baseline/B87_materiali19/mods')
_c = {}
def img(tid, xbox):
    k = (tid, xbox)
    if k in _c: return _c[k]
    m = texlib.xb_mean(tid) if xbox else texlib.pc_mean(tid)
    r = None
    if m is not None and not m['cube'] and m['rgba'] is not None:
        if xbox:
            d, _ = texlib.xb_sec(tid); h, res, _ = TC.xbox_levels(d)
            kind = m['kind']; im = TC.blocks_to_image(res[0][0], kind, h['w'], h['h']).astype(np.float32) / 255.
            if kind == 'DXT1': im[..., 3] = 1.
            if kind == 'DXN': im = np.stack([im[..., 0], im[..., 1], np.zeros_like(im[..., 0]), np.ones_like(im[..., 0])], -1)
        else:
            d, _ = texlib.pc_sec(tid); im = TC.pc_image(d, 0, 0).astype(np.float32) / 255.
        r = im
    _c[k] = r; return r

def mk_tex(rows):   # rows: slot -> (tid, xbox)
    def f(smp, coords, mode):
        tid, xb = rows.get(smp, (None, None)); n = coords.shape[0]
        im = img(tid, xb) if tid is not None else None
        if im is None:
            m = (texlib.xb_texel(tid) if xb else texlib.pc_texel(tid)) if tid is not None else None
            v = np.array([.5, .5, .5, 1.]) if m is None else m
            return np.tile(np.asarray(v, np.float32), (n, 1))
        h, w = im.shape[:2]; u = np.mod(coords[:, 0], 1.0); v = np.mod(coords[:, 1], 1.0) if coords.shape[1] > 1 else u
        return im[np.clip((v * h).astype(int), 0, h - 1), np.clip((u * w).astype(int), 0, w - 1)]
    return f

def run(prog, matp, tex, seed=11, N=4096):
    env = F9.Env(seed, matp, N=N); env.tex = tex
    st, kill = env.run(prog, F9.body(prog), env.state0(prog), {})
    c = st.get((sm3asm.RT_COLOROUT, 0))
    return None if c is None else c[~kill] if kill is not None and (~kill).any() else c

def summ(c):
    if c is None: return 'None'
    lum = c[:, :3].mean(1); a = c[:, 3]
    return 'RGB=%s alfa p50/p90=%s  lum p50/p90/p99=%s  bianchi(lum>.7)=%.3f  premult(rgb*a) medio=%s' % (
        np.round(c[:, :3].mean(0), 3), np.round(np.percentile(a, [50, 90]), 3), np.round(np.percentile(lum, [50, 90, 99]), 3), float((lum > .7).mean()),
        np.round((c[:, :3] * np.clip(a, 0, 1)[:, None]).mean(0), 3))

def main(rel, mid):
    s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
    pe = C.entries(s.data, s.reloc, 'le'); xe = C.entries(*DM[mid], 'be')
    xl = struct.unpack_from('>4I', DM[mid][0], 0x28); pl = struct.unpack_from('<4I', s.data, 0x28)
    xrows = {e['slot']: (e['tex'], True) for e in xe}; prow = {e['slot']: (e['tex'], False) for e in pe}
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(s, 'le')
    secs = {(x.type, x.id): x for x in tree[rel].sections}
    fn = C.frame_lib(secs[(9, pl[2])].data)
    print('== materiale', mid, rel)
    for k in (0, 1):
        xblob = D[xl[2]]['entries'][D[xl[2]]['slots'][k]]['blob']
        K = F9.Consts([]); o = dict(B.material_opts(mid))
        px = F9.translate_x(xblob, K.fn, lambda n, c: c, F9.xbools(xblob), opts=o)[0]
        print('  Xbox var%d (opts %s): %s' % (k, sorted(o), summ(run(px, XPm, mk_tex(xrows)))))
        o2 = dict(o); o2.pop('alpha1', None)
        px2 = F9.translate_x(xblob, F9.Consts([]).fn, lambda n, c: c, F9.xbools(xblob), opts=o2)[0]
        print('  Xbox var%d SENZA alpha1: %s' % (k, summ(run(px2, XPm, mk_tex(xrows)))))
        kk = k
        print('  PC surrogato var%d: %s' % (kk, summ(run(sm3asm.decode(fn['entries'][fn['slots'][kk]]['bc']), PPm, mk_tex(prow)))))

if __name__ == '__main__':
    for spec in sys.argv[1:]:
        r, m = spec.split(':'); main(r, int(m))
