import sys, os
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import assemble_dlc as A, dlc_generic as DG, generic_store, analog_idcoin
from convert_dlc import raw_dlc
from drm import cdrm_decode, sections_with_data
store = generic_store.load(); ids = DG.DlcIds(store, None)
raw, _ = raw_dlc('streamgroups\\dlc_dungeon_dungeon_main.drm')
h, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
for ef in (False, True):
    secs, rep = DG.convert_drm(xs, ids, store, A.make_media('silence', 'dlc'), extra_fixes=ef)   # NO assemble guard around it
    s = [q for q in secs if q.type == 7 and q.id in (23793, 23796)]
    print('direct DG.convert_drm extra_fixes=%s' % ef, [q.data[0x10:0x14].hex() for q in s], 'guard left active:', DG._analog_build is analog_idcoin._build_guarded)
