"""Validate tex_convert on base-game Xbox<->PC texture pairs.
python -I tex_validate.py [limit_names] -> work/textures/validate.json + summary"""
import sys, os, json, collections, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from multiprocessing import Pool
W = '/path/to/trudlcport/work/textures/'


def psnr(a, b):
    m = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if m == 0 else 10 * math.log10(255 * 255 / m)


def check(xd, pdat):
    import tex_convert as T
    xh = T.parse_xbox(xd); ph = T.parse_pc(pdat)
    r = dict(xfmt=xh['fmtname'], pfmt=T.pc_kind(ph['fmt']) if ph['fmt'] in (0x15, *T.FOURCC.values()) else hex(ph['fmt']),
             w=xh['w'], h=xh['h'], mips=xh['mips'], flags=xh['flags'], pw=ph['w'], ph=ph['h'], pmips=ph['mips'])
    try:
        _, _, need = T.xbox_levels(xd)
        r['xsize_ok'] = need == len(xd) - 24
        r['xsize'] = len(xd) - 24; r['need'] = need
        out = T.convert(xd)
    except Exception as e:
        r['err'] = repr(e)[:120]; return r
    r['exact'] = out == pdat
    r['hdr_exact'] = out[:24] == pdat[:24]
    if (xh['w'], xh['h']) != (ph['w'], ph['h']) or r['pfmt'] not in ('DXT1', 'DXT3', 'DXT5', 'ARGB'):
        return r
    ch, ck, cres = T.pc_levels(out)
    hh, hk, hres = T.pc_levels(pdat)
    r['ckind'] = ck
    if ck == hk:
        tot = eq = 0; lv = []
        nl = min(len(cres[0]), len(hres[0]))
        for f in range(min(len(cres), len(hres))):
            for l in range(nl):
                a, b = cres[f][l][0], hres[f][l][0]
                if a.shape != b.shape: continue
                e = int((a == b).all(1).sum()); tot += len(a); eq += e
                if f == 0: lv.append(round(e / len(a), 4))
        r['blk_match'] = eq / max(1, tot); r['lvl_match'] = lv
        r['data_exact'] = out[24:] == pdat[24:]
    # PSNR on decoded base (face 0) and on the smallest common mip >= 4x4
    ia = T.blocks_to_image(cres[0][0][0], ck, cres[0][0][1], cres[0][0][2])
    ib = T.blocks_to_image(hres[0][0][0], hk, hres[0][0][1], hres[0][0][2])
    r['psnr_rgb'] = psnr(ia[..., :3], ib[..., :3]); r['psnr_a'] = psnr(ia[..., 3], ib[..., 3])
    if ck == 'DXT5' and xh['fmtname'] == 'DXN':
        r['psnr_r'] = psnr(ia[..., 0], ib[..., 0]); r['psnr_g'] = psnr(ia[..., 1], ib[..., 1])
    return r


def do(name):
    from tex_pairs import tex_pairs
    out = []
    try:
        for k, a, b in tex_pairs(name):
            r = check(a['data'], b['data']); r['name'] = name; r['k'] = k
            out.append(r)
    except Exception as e:
        out.append(dict(name=name, k=-1, err=repr(e)[:200]))
    return out


def summary(R):
    C = collections.Counter
    print('total pairs', len(R), 'errors', sum('err' in r for r in R), C(r.get('err', '')[:60] for r in R if 'err' in r).most_common(5))
    ok = [r for r in R if 'err' not in r]
    print('xbox size == layout size', C(r['xsize_ok'] for r in ok))
    bad = [r for r in ok if not r['xsize_ok']]
    print('  size mismatches', C((r['xfmt'], r['w'], r['h'], r['mips'], r['flags'], r['xsize'], r['need']) for r in bad).most_common(10))
    same = [r for r in ok if (r['w'], r['h']) == (r['pw'], r['ph']) and r['mips'] == r['pmips']]
    print('same dims+mips', len(same), 'of', len(ok))
    print('%-22s %6s %7s %7s %8s %8s %8s' % ('xfmt->pcfmt(flags)', 'n', 'exact', 'hdr_ok', 'blk%', 'psnrRGB', 'psnrA'))
    groups = collections.defaultdict(list)
    for r in same: groups[(r['xfmt'], r['pfmt'], hex(r['flags']))].append(r)
    for key, g in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        bm = [r['blk_match'] for r in g if 'blk_match' in r]
        pr = sorted(r['psnr_rgb'] for r in g if 'psnr_rgb' in r)
        pa = sorted(r['psnr_a'] for r in g if 'psnr_a' in r)
        print('%-22s %6d %7d %7d %8s %8s %8s' % ('%s->%s(%s)' % key, len(g), sum(r['exact'] for r in g), sum(r['hdr_exact'] for r in g),
              '%.4f' % (sum(bm) / len(bm)) if bm else '-', '%.1f' % pr[len(pr) // 2] if pr else '-', '%.1f' % pa[len(pa) // 2] if pa else '-'))
    return same


if __name__ == '__main__':
    from tex_pairs import pair_names
    names = pair_names()
    if len(sys.argv) > 1: names = names[:int(sys.argv[1])]
    with Pool(8) as p: res = p.map(do, names, chunksize=2)
    R = [r for rr in res for r in rr]
    json.dump(R, open(W + 'validate.json', 'w'))
    summary(R)
