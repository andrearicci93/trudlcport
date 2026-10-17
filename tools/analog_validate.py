"""Leave-one-out validation of dlc_generic.analog_convert on base pairs: treat the DTPs of an Xbox base DRM as DLC-new
(its own ids excluded from the analog search), rebuild them from the PC analog and compare with the real PC sections.
usage: tools/venv/bin/python -I tools/analog_validate.py lara_bikini.drm lara_casual.drm ..."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG, generic_store, drm_write as DW, drm_reloc as R
from drm import cdrm_decode, sections_with_data
from rung1 import raw_pc, raw_xbox
store = generic_store.load(); ids = DG.DlcIds(store, None)
tot = collections.Counter()
for name in sys.argv[1:]:
    rx = raw_xbox(name)
    if rx is None: print(name, 'not in Xbox base'); continue
    _, xs = sections_with_data(cdrm_decode(rx, 'be'), 'be')
    P = DW.read(raw_pc(name), 'le'); pm = {(s.type, s.id): s for s in P.sections}
    ids.local = {}
    own = {s['id'] for s in xs if s['type'] == 7}
    for s in xs:
        if s['type'] != 7: continue
        res = DG.analog_convert(s, xs, ids, store, exclude=own)
        if res is None: tot['no_analog'] += 1; continue
        data, reloc, ax = res
        q = pm.get((7, ids.base[7].get(s['id'])))
        if q is None: tot['no_pc'] += 1; continue
        ok = (data == q.data, reloc == q.reloc)
        tot['data_exact' if ok[0] else 'data_WRONG'] += 1; tot['reloc_exact' if ok[1] else 'reloc_WRONG'] += 1
        if not all(ok) or len(data) != len(s['data']):
            nw = sum(data[i:i+4] != q.data[i:i+4] for i in range(0, min(len(data), len(q.data)), 4))
            print(name, s['id'], 'analog', ax, 'size x/out/pc', len(s['data']), len(data), len(q.data), 'exact', ok, 'wrong words', nw)
print(dict(tot), dict(DG.ANALOG_STATS))
