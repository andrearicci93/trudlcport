"""Second pass for tex_match leftovers: best decoded PSNR against same-dims PC textures in the same DRM."""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
W = '/path/to/trudlcport/work/textures/'


def do(item):
    name, ks = item
    from pairs import pc_drm, xbox_drm
    import tex_convert as T
    from tex_validate import psnr
    p = pc_drm(name); x = xbox_drm(name)
    ps = [s for s in p[1] if s['type'] == 5]; xs = [s for s in x[1] if s['type'] == 5]
    pimgs = []
    for s in ps:
        h = T.parse_pc(s['data'])
        try: pimgs.append(((h['w'], h['h']), T.pc_image(s['data'])))
        except Exception: pass
    out = []
    for k in ks:
        xh = T.parse_xbox(xs[k]['data'])
        ci = T.pc_image(T.convert(xs[k]['data']))
        best = max([psnr(ci[..., :3], im[..., :3]) for d, im in pimgs if d == (xh['w'], xh['h'])] or [-1])
        out.append(dict(name=name, k=k, fmt=xh['fmtname'], w=xh['w'], h=xh['h'], best=best))
    return out


if __name__ == '__main__':
    R = json.load(open(W + 'match.json'))
    left = collections.defaultdict(list)
    for r in R:
        if r.get('fmt') != 'DXN' and 'err' not in r and not r['any']: left[r['name']].append(r['k'])
    with Pool(8) as p: res = p.map(do, list(left.items()), chunksize=1)
    O = [r for rr in res for r in rr]
    json.dump(O, open(W + 'match2.json', 'w'))
    b = [r['best'] for r in O]
    C = collections.Counter
    print('leftovers', len(O), 'best RGB PSNR buckets', C(('>=40' if v >= 40 else '30-40' if v >= 30 else '20-30' if v >= 20 else '<20') for v in b))
    print('<20 examples', [(r['name'], r['k'], r['fmt'], r['w'], r['h'], round(r['best'], 1)) for r in O if r['best'] < 20][:15])
