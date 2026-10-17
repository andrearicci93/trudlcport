import sys, io, contextlib, struct
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
F10, C, L = W.F10, W.C, W.L; DM = L['DM']
tree = C.read_tree(sys.argv[1]); rel = sys.argv[2]
secs = {(s.type, s.id): s for s in tree[rel].sections}
for mid in map(int, sys.argv[3:]):
    ms = secs[(10, mid)]
    X = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); P = F10.params(ms, 'le')
    print('== mat', mid, 'libX', struct.unpack_from('>4I', DM[mid][0], 0x28), 'libPC', struct.unpack_from('<4I', ms.data, 0x28))
    for j in range(max(len(X), len(P))):
        print('  %2d  X=%-30s PC=%s' % (j, np.round(X[j], 3).tolist() if j < len(X) else '-', np.round(P[j], 3).tolist() if j < len(P) else '-'))
