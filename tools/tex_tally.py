"""Tally texture headers over all base-game pairs and over DLC DRMs.
python -I tex_tally.py pairs|dlc  -> work/textures/hdr_pairs.json / hdr_dlc.json"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
W = '/path/to/trudlcport/work/'

def xinfo(d):
    from tex_convert import parse_xbox
    h = parse_xbox(d); h['magic'] = h['magic'].decode('latin1'); h['dsize'] = len(d) - 24
    return h

def pinfo(d):
    from tex_convert import parse_pc
    h = parse_pc(d); h['magic'] = h['magic'].decode('latin1'); h['dsize'] = len(d) - 24
    return h

def do_pair(name):
    from tex_pairs import tex_pairs
    try:
        return [(name, k, a['id'], b['id'], xinfo(a['data']), pinfo(b['data'])) for k, a, b in tex_pairs(name)]
    except Exception as e:
        return [(name, -1, 0, 0, repr(e), None)]

def do_dlc(args):
    path, i = args
    from archive import Archive
    from drm import cdrm_decode, sections_with_data
    a = Archive(path, 'be')
    raw = cdrm_decode(a.read(a.idx[i]), 'be')
    h, secs = sections_with_data(raw, 'be')
    return [(path.split('/')[-1], i, a.idx[i]['hash'], s['i'], s['id'], xinfo(s['data'])) for s in secs if s['type'] == 5]

if __name__ == '__main__':
    os.makedirs(W + 'textures', exist_ok=True)
    if sys.argv[1] == 'pairs':
        from tex_pairs import pair_names
        names = pair_names()
        with Pool(8) as p: res = p.map(do_pair, names, chunksize=4)
        out = [r for rr in res for r in rr]
        json.dump(out, open(W + 'textures/hdr_pairs.json', 'w'))
        print(len(out), 'texture pairs')
    else:
        idx = json.load(open(W + 'idx_dlc.json'))
        jobs = [(r[0], r[1]) for r in idx if isinstance(r[5], list) and any(s[0] == 5 for s in r[5])]
        with Pool(8) as p: res = p.map(do_dlc, jobs, chunksize=4)
        out = [r for rr in res for r in rr]
        json.dump(out, open(W + 'textures/hdr_dlc.json', 'w'))
        print(len(jobs), 'dlc drms', len(out), 'texture sections')
