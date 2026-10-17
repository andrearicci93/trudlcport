import sys, os
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import dlc_generic as DG, generic_store, analog_idcoin, drm_write as DW
from convert_dlc import raw_dlc
from drm import cdrm_decode, sections_with_data
store = generic_store.load(); ids = DG.DlcIds(store, None)
raw, _ = raw_dlc('streamgroups\\dlc_dungeon_dungeon_main.drm')
h, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
W = os.path.expanduser('~/Downloads/tru-port/work/')
def count(path, guard):
    D = DW.read(open(path, 'rb').read(), 'le'); n = 0
    import contextlib
    with (analog_idcoin.guarded() if guard else contextlib.nullcontext()):
        for s in xs:
            if s['type'] != 7 or s['data'] is None: continue
            ids.local = {}
            r = DG.analog_convert(s, xs, ids, store)
            if r is None: continue
            o = [q for q in D.sections if q.type == 7 and q.id == ids(7, s['id'])]
            if o and r[0] != o[0].data: n += 1
    return n
for lab, p, g in (('fresh3 unguarded', 'ws/integ/out_fresh3', 0), ('fresh3 guarded', 'ws/integ/out_fresh3', 1), ('B8 unguarded', 'baseline/B8/mods', 0), ('fresh2 unguarded', 'ws/rebuild/out_fresh2', 0)):
    print(lab, count(W + p + '/streamgroups/dlc_dungeon_dungeon_main.drm', g))
