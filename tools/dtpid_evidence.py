"""Base-pair evidence for tools/dtpid_sweep.py: for every base Xbox/PC DRM pair (work/generic/pairs.pkl), every DTP word
(4-aligned, not a pointer / id-ref reloc slot) whose Xbox value is the id of a DTP section of the SAME Xbox DRM and is
remapped on PC (ids(7,v) != v): PC class of that word.  Output work/generic/dtpid_evidence.pkl
{value: [n, n_remapped]} + overall precision of the sweep rule.
usage: tools/venv/bin/python -I tools/dtpid_evidence.py"""
import sys, os, struct, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import aidata_fix as A
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
OUT = os.path.join(W, 'dtpid_evidence.pkl')

def main():
    import dlc_generic as DG, generic_store
    ids = DG.DlcIds(generic_store.load(), None); bm = ids.base[7]
    pairs = pickle.load(open(os.path.join(W, 'pairs.pkl'), 'rb'))
    ev = collections.defaultdict(lambda: [0, 0]); tot = collections.Counter()
    for nm, (X, P) in pairs.items():
        if X is None or not isinstance(P, tuple): continue
        xdtp = {s['id'] for s in X[1] if s['type'] == 7}
        ps = [p for p in P[1] if p['type'] == 7 and p['data'] is not None]
        for s in X[1]:
            if s['type'] != 7 or s['data'] is None: continue
            pc = A._pc_twin(s, ps)
            if pc is None or len(pc['data']) != len(s['data']): continue
            rel = R.parse(s['reloc'], 'be'); skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
            xd = s['data']; n = len(xd) // 4
            xw = struct.unpack_from('>%dI' % n, xd); pw = struct.unpack_from('<%dI' % n, pc['data'])
            for i, v in enumerate(xw):
                if v not in xdtp or 4 * i in skip: continue
                m = bm.get(v)
                if m is None or m == v: continue
                e = ev[v]; e[0] += 1; ok = pw[i] == m; e[1] += ok
                tot['words'] += 1; tot['remapped'] += ok
    pickle.dump(dict(ev), open(OUT, 'wb'))
    print('rule precision on base pairs:', dict(tot), '%.2f%%' % (100.0 * tot['remapped'] / max(1, tot['words'])), 'values', len(ev))

if __name__ == '__main__':
    main()
