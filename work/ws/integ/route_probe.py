import sys, os
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import assemble_dlc as A, dlc_generic as DG, generic_store, analog_idcoin
from drm import cdrm_decode, sections_with_data
from archive import Archive
from names import crc
PACK10 = os.path.expanduser('~/Downloads/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000')
store = generic_store.load(); ids = DG.DlcIds(store, None); arc = Archive(PACK10, 'be')
T = {'dlc1_uo_dragon_slider.drm': [20457], 'dlc1_uo_raft_bridge.drm': [20765], 'dlc_dungeonhalla.drm': [20493], 'dlc_dungeonhallb.drm': [20133],
     'dlc_caverns.drm': [20872], 'streamgroups\\dlc_dungeon_dungeon_main.drm': [], 'dlc_dungeon.drm': []}
for rel, xidl in T.items():
    raw = arc.read([r for r in arc.find(crc('xenon-w\\' + rel)) if r['spec'] == 0xffffffff][0])
    h, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
    with analog_idcoin.guarded():
        secs, rep = DG.convert_drm(xs, ids, store, A.make_media('silence', 'dlc'), extra_fixes=True)
    for k, t, xid, nid, route in rep:
        if (t == 7 and xid in xidl) or (rel.endswith('dungeon_main.drm') and t == 7 and 23793 <= nid <= 23796) or (rel == 'dlc_dungeon.drm' and t == 0 and k in (47, 51)):
            print(rel, 'k', k, 'type', t, 'xid', xid, 'pc', nid, 'route', route)
