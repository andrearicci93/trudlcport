"""Extract unique matched Xbox<->PC section pairs of generic types (0,7,8,13) from the pair cache
-> work/script/pairs_<type>.pkl : list of dict(name, xi, pj, xd, xr, pd, pr, xid, pid, ext=[(type,xid)], extp=[(type,pid)]).
Dedupe by (Xbox data, Xbox reloc) hash. Usage: tools/venv/bin/python -I tools/script_pairs.py"""
import sys, os, pickle, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
from generic_ids import section_matches
from generic_cache import load_pairs
from convert_generic import IdMapper
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'script')
if __name__ == '__main__':
    P = load_pairs(); idm = IdMapper().m
    res = collections.defaultdict(list); seen = set()
    for nm in sorted(P):
        (xh, sx), (ph, sp) = P[nm]
        for i, j, st in section_matches(sx, sp, idm):
            a, b = sx[i], sp[j]
            t = a['type']
            if t not in (0, 7, 8, 13) or a['data'] is None or b['data'] is None: continue
            rx = R.parse(a['reloc'], 'be'); rp = R.parse(b['reloc'], 'le')
            ext = [(sx[si]['type'], sx[si]['id'], so, do) for si, so, do in rx.external]
            extp = [(sp[si]['type'], sp[si]['id'], so, do) for si, so, do in rp.external]
            h = hashlib.md5(a['data'] + a['reloc'] + repr(ext).encode()).digest()
            if h in seen: continue
            seen.add(h)
            res[t].append(dict(name=nm, xi=i, pj=j, st=st, xd=a['data'], xr=a['reloc'], pd=b['data'], pr=b['reloc'],
                               xid=a['id'], pid=b['id'], ext=ext, extp=extp, xver=a['ver'], pver=b['ver']))
    os.makedirs(OUT, exist_ok=True)
    for t, l in res.items():
        pickle.dump(l, open(os.path.join(OUT, 'pairs_%d.pkl' % t), 'wb'))
        print(t, len(l), 'same size', sum(len(r['xd']) == len(r['pd']) for r in l), flush=True)
