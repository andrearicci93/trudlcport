"""cmp_tree.py A B [--words] : compare two DRM trees (same relpaths) section by section, words list per file"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmp as C
A, B = sys.argv[1:3]; verbose = '--words' in sys.argv
fa = sorted(os.path.relpath(os.path.join(d, f), A) for d, _, fs in os.walk(A) for f in fs if f.endswith('.drm'))
fb = sorted(os.path.relpath(os.path.join(d, f), B) for d, _, fs in os.walk(B) for f in fs if f.endswith('.drm'))
print('files A', len(fa), 'B', len(fb), 'only A', sorted(set(fa) - set(fb))[:5], 'only B', sorted(set(fb) - set(fa))[:5])
tot = 0; nf = 0; rows = []
for rel in fa:
    if rel not in set(fb): continue
    ba, bb = open(os.path.join(A, rel), 'rb').read(), open(os.path.join(B, rel), 'rb').read()
    if ba == bb: continue
    d = C.diff(os.path.join(A, rel), os.path.join(B, rel)); nf += 1; tot += len(d)
    print(rel, len(d)); rows.append((rel, d))
    if verbose:
        for x in d[:40]: print('    ', x)
print('files differing', nf, 'diff items', tot)
