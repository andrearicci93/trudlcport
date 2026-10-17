"""Scope scan: for every DLC DRM already converted in the given dirs, list DLC-new DTPs (Xbox id not a base id) that
dlc_generic.analog_convert can rebuild from a PC analog, and whether the PC analog is RE-AUTHORED (size differs: the old
'convert' route certainly produced a wrong layout for those).  usage: analog_scan.py DIR [DIR..]"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG, generic_store
from drm import cdrm_decode, sections_with_data
from convert_dlc import raw_dlc
store = generic_store.load(); ids = DG.DlcIds(store, None)
names = sorted({f for d in sys.argv[1:] for r, _, fs in os.walk(d) for f in fs if f.endswith('.drm')})
tot = collections.Counter()
for nm in names:
    raw, _ = raw_dlc(nm)
    if raw is None: continue
    _, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
    ids.local = {}
    hit = []
    for s in xs:
        if s['type'] != 7 or s['id'] in ids.base.get(7, {}): continue
        tot['dlc_new_dtp'] += 1
        r = DG.analog_convert(s, xs, ids, store)
        if r is None: continue
        re = len(r[0]) != len(s['data'])
        tot['analog_reauthored' if re else 'analog_same_size'] += 1
        hit.append((s['id'], len(s['data']), len(r[0]), r[2]))
    if hit: print(nm, hit)
print(dict(tot), dict(DG.ANALOG_STATS))
