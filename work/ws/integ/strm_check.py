import sys, os
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import streamname_fix as S
d = sys.argv[1]; n = hit = skip = 0
for r, _, fs in os.walk(d):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(r, f), d).replace('\\', '/')
        raw = open(os.path.join(r, f), 'rb').read()
        xs = S.xsecs_of(rel)
        if xs is None: skip += 1; print('NO XBOX SOURCE', rel); continue
        try: _, log = S.fix_section(rel, raw)
        except Exception as e: print('ERR', rel, e); continue
        n += 1
        for l in log: hit += 1; print('FIX NEEDED', rel, l[0], l[1], l[2][:60], '->', l[3][:60])
print(d, 'files', n, 'skipped', skip, 'sections needing fix', hit)
