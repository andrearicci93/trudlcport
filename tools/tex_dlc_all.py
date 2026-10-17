"""Convert every texture section in all DLC DRMs (pack10/pack11 via work/idx_dlc.json) as a sanity check:
layout size == Xbox data size, conversion succeeds. Prints per-format stats.
python -I tex_dlc_all.py"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
W = '/path/to/trudlcport/work/'


def do(args):
    path, i = args
    from archive import Archive
    from drm import cdrm_decode, sections_with_data
    import tex_convert as T
    a = Archive(path, 'be')
    raw = cdrm_decode(a.read(a.idx[i]), 'be')
    h, secs = sections_with_data(raw, 'be')
    out = []
    for s in secs:
        if s['type'] != 5: continue
        xh = T.parse_xbox(s['data'])
        r = dict(pack=path.split('/')[-1], drm=i, sec=s['i'], id=s['id'], fmt=xh['fmtname'], d3dfmt=hex(xh['d3dfmt']),
                 w=xh['w'], h=xh['h'], mips=xh['mips'], flags=xh['flags'], xsize=s['size'] - 24)
        try:
            _, _, need = T.xbox_levels(s['data'])
            r['size_ok'] = need == s['size'] - 24
            r['pcsize'] = len(T.convert(s['data']))
        except Exception as e:
            r['err'] = repr(e)[:100]
        out.append(r)
    return out


if __name__ == '__main__':
    idx = json.load(open(W + 'idx_dlc.json'))
    jobs = [(r[0], r[1]) for r in idx if isinstance(r[5], list) and any(s[0] == 5 for s in r[5])]
    with Pool(8) as p: res = p.map(do, jobs, chunksize=2)
    R = [r for rr in res for r in rr]
    json.dump(R, open(W + 'textures/dlc_all.json', 'w'))
    C = collections.Counter
    print('DLC DRMs with textures', len(jobs), 'texture sections', len(R), 'errors', sum('err' in r for r in R),
          C(r['err'] for r in R if 'err' in r).most_common(3))
    print('layout size ok', C(r.get('size_ok') for r in R))
    for pack in sorted({r['pack'] for r in R}):
        P = [r for r in R if r['pack'] == pack]
        u = {}
        for r in P: u[r['id']] = r
        print(pack, 'sections', len(P), 'unique ids', len(u))
        print('  formats (sections)', C((r['fmt'], r['d3dfmt']) for r in P).most_common())
        print('  formats (unique)  ', C(r['fmt'] for r in u.values()).most_common(),
              'cubemaps', sum(1 for r in u.values() if r['flags'] & 0x8000),
              'no-mip', sum(1 for r in u.values() if r['mips'] == 0))
        print('  dims (unique)', C('%dx%d' % (r['w'], r['h']) for r in u.values()).most_common(12))
