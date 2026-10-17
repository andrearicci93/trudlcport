"""Pairing / quality check for override_merge outputs (the D:=X selftest cannot detect a WRONG X<->P pairing).

For the pack11 g_pda / camerashakes merge:
  a) 'pc_same' textures: tex_convert.convert(DLC Xbox texture) vs the copied PC texture: byte-equal, else same header + PSNR
  b) 'pc_same' generic sections (types 2,7,8,11) of equal size: learned/route conversion of the Xbox section vs the copied
     PC section, % equal 32-bit words (correct pairs ~95-100%, a wrong pairing scores low)
  c) sections we SHIP converted (convert/template routes): the same conversion applied to the Xbox BASE version of that
     section vs the PC BIGFILE version (pre-patch) -> exact / word agreement = expected quality of the shipped section
Usage: tools/venv/bin/python -I tools/override_check.py [g_pda.drm camerashakes.drm]
"""
import sys, os, collections, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import override_merge as OM, dlc_generic as DG, generic_store, drm_reloc as R
from generic_ids import section_matches
from generic_store import norm_hash

def words_eq(a, b):
    n = min(len(a), len(b)) // 4
    return sum(1 for i in range(n) if a[4 * i:4 * i + 4] == b[4 * i:4 * i + 4]) / max(1, n)

def psnr(a, b):
    import numpy as np
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if a.shape != b.shape: return -1
    m = ((a - b) ** 2).mean()
    return 99.0 if m == 0 else 10 * math.log10(255 ** 2 / m)

def check(name, pack='pack11'):
    import tex_convert
    ids = DG.DlcIds(); store = generic_store.load()
    drm, rep = OM.merge(name, pack, ids=ids, store=store)
    _, _, D = OM.load((pack,), name)
    _, _, X = OM.load(('tu', 'xl1', 'xl2'), name)
    _, _, PB = OM.load(('pcbig',), name)
    st = collections.Counter(); low = []
    route = rep['route']
    conv, crep = DG.convert_drm(D, ids, store, media=None, use_pc_copy=False, use_template=False)
    for k, s in enumerate(D):
        out = drm.sections[k]; t = s['type']; r = route[k]
        if r == 'pc_same' and t == 5:
            try:
                c = tex_convert.convert(s['data'])
            except Exception:
                st['tex_unsupported'] += 1; continue
            if out.data == c: st['tex_byte_equal'] += 1; continue
            try:
                p = psnr(tex_convert.pc_image(out.data), tex_convert.pc_image(c))
            except Exception:
                p = -1
            st['tex_psnr>=30' if p >= 30 else 'tex_psnr<30_or_dims_differ'] += 1
            if p < 30: low.append(('tex', s['id'], out.id, round(p, 1)))
        elif r == 'pc_same' and t in (2, 7, 8, 11):
            if len(out.data) != len(conv[k].data): st['generic_pc_same_size_differs'] += 1; continue
            w = words_eq(out.data, conv[k].data)
            st['generic_pc_same_n'] += 1; st['generic_pc_same_wordsum'] += w; st['generic_pc_same_exact'] += out.data == conv[k].data
            if w < 0.85: low.append((t, s['id'], out.id, round(w, 3)))
    # c) sections shipped converted: same pure conversion of the Xbox BASE version vs PC BIGFILE version
    mt = section_matches(X, PB, ids.base); x2pb = {i: j for i, j, _ in mt}
    pby = {(p['type'], p['id']): p for p in PB}
    cx, _ = DG.convert_drm(X, ids, store, media=None, use_pc_copy=False, use_template=False)
    xi = {(x['type'], x['id']): i for i, x in enumerate(X)}
    for k, s in enumerate(D):
        if route[k] == 'pc_same' or s['type'] not in (7, 8): continue
        st['shipped_converted_%d' % s['type']] += 1
        i = xi.get((s['type'], s['id']))
        if i is None: st['shipped_dlc_new_%d' % s['type']] += 1; continue
        pb = PB[x2pb[i]] if i in x2pb else pby.get((s['type'], ids(s['type'], s['id'])))
        if pb is None or len(pb['data']) != len(cx[i].data): st['shipped_no_pc_reference'] += 1; continue
        w = words_eq(cx[i].data, pb['data'])
        st['shipped_ref_n'] += 1; st['shipped_ref_exact'] += cx[i].data == pb['data']; st['shipped_ref_wordsum'] += w
    for key in [k for k in list(st) if k.endswith('_wordsum')]:
        n = st[key.replace('_wordsum', '_n')]
        st[key.replace('_wordsum', '_mean_word_agreement')] = round(st.pop(key) / max(1, n), 4)
    print(name, pack, dict(st))
    print('   low scorers:', low[:20])

if __name__ == '__main__':
    for n in [a for a in sys.argv[1:] if a.endswith('.drm')] or ['g_pda.drm', 'camerashakes.drm']:
        check(n)
