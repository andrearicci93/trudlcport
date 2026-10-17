#!/usr/bin/env python3
"""Compare a mods/ folder against docs/data/B90_gold_L4.manifest.tsv (relpath, size, md5).
usage: python3 scripts/verify_mods.py /path/to/mods   -> prints missing / different / extra files"""
import sys, os, hashlib
here = os.path.dirname(os.path.abspath(__file__)); mods = sys.argv[1]
want = {}
for l in list(open(os.path.join(here, '..', 'docs', 'data', 'B90_gold_L4.manifest.tsv')))[1:]:
    r = l.rstrip('\n').split('\t'); want[r[0].lower()] = (int(r[1]), r[2])
seen = set(); miss = diff = 0
for rel, (size, md5) in want.items():
    p = os.path.join(mods, rel.replace('/', os.sep))
    cand = p if os.path.exists(p) else None
    if cand is None: print('MISSING  ', rel); miss += 1; continue
    h = hashlib.md5(open(cand, 'rb').read()).hexdigest()
    if os.path.getsize(cand) != size or h != md5: print('DIFFERENT', rel); diff += 1
extra = []
for dp, _, fs in os.walk(mods):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), mods).replace(os.sep, '/')
        if rel.lower() not in want: extra.append(rel)
print('missing %d, different %d, extra %d (of %d expected)' % (miss, diff, len(extra), len(want)))
for e in extra[:20]: print('EXTRA    ', e)
