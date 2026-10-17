"""Position-independent validation: is convert(xbox texture) byte-identical to ANY PC texture section of the
same DRM? (sections are not always position-parallel). python -I tex_match.py -> work/textures/match.json"""
import sys, os, json, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
W = '/path/to/trudlcport/work/textures/'


def do(name):
    from pairs import pc_drm, xbox_drm
    import tex_convert as T
    p = pc_drm(name); x = xbox_drm(name)
    if not p or not x: return []
    ps = [s for s in p[1] if s['type'] == 5]; xs = [s for s in x[1] if s['type'] == 5]
    pset = {hashlib.sha1(s['data']).digest() for s in ps}
    pdata = {(T.parse_pc(s['data'])['w'], T.parse_pc(s['data'])['h']): None for s in ps}
    out = []
    for k, s in enumerate(xs):
        xh = T.parse_xbox(s['data'])
        try:
            c = T.convert(s['data'])
        except Exception as e:
            out.append(dict(name=name, k=k, fmt=xh['fmtname'], err=repr(e)[:80])); continue
        pos = k < len(ps) and ps[k]['data'] == c
        anyx = hashlib.sha1(c).digest() in pset
        out.append(dict(name=name, k=k, fmt=xh['fmtname'], w=xh['w'], h=xh['h'], flags=xh['flags'], pos=pos, any=anyx,
                        dims_in_pc=(xh['w'], xh['h']) in pdata))
    return out


if __name__ == '__main__':
    from tex_pairs import pair_names
    with Pool(8) as p: res = p.map(do, pair_names(), chunksize=2)
    R = [r for rr in res for r in rr]
    json.dump(R, open(W + 'match.json', 'w'))
    C = collections.Counter
    nd = [r for r in R if r.get('fmt') != 'DXN' and 'err' not in r]
    print('xbox textures', len(R), 'non-DXN', len(nd))
    print('positional exact', sum(r['pos'] for r in nd), 'exact to some PC texture in same DRM', sum(r['any'] for r in nd))
    for f in sorted({r['fmt'] for r in nd}):
        g = [r for r in nd if r['fmt'] == f]
        print('  %-8s n=%5d pos=%5d any=%5d' % (f, len(g), sum(r['pos'] for r in g), sum(r['any'] for r in g)))
    cube = [r for r in nd if r['flags'] & 0x8000]
    print('  cubemaps n=%d pos=%d any=%d' % (len(cube), sum(r['pos'] for r in cube), sum(r['any'] for r in cube)))
    left = [r for r in nd if not r['any']]
    print('unmatched', len(left), 'of which dims also present in PC DRM', sum(r['dims_in_pc'] for r in left))
