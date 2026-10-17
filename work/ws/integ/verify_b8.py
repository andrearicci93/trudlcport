import sys, os, struct
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import drm_write as DW
W = os.path.expanduser('~/Downloads/tru-port/work/')
B8 = W + 'baseline/B8/mods/'; F3 = 'out_fresh3/'; F2 = W + 'ws/rebuild/out_fresh2/'
def sec(D, t, i, idx):
    if t == 0: return D.sections[idx]
    return [s for s in D.sections if s.type == t and s.id == i][0]
rows = []
def add(name, rel, t, i, idx, offs):
    d3, d2, d8 = [DW.read(open(b + rel, 'rb').read(), 'le') for b in (F3, F2, B8)]
    s3, s2, s8 = sec(d3, t, i, idx), sec(d2, t, i, idx), sec(d8, t, i, idx)
    for o in offs:
        rows.append((name, rel, 'type%d id%d idx%d' % (t, i, idx), hex(o), s2.data[o:o+4].hex(), s8.data[o:o+4].hex(), s3.data[o:o+4].hex(), s3.data[o:o+4] == s8.data[o:o+4]))
add('(1) matIdx dungeon_main', 'streamgroups/dlc_dungeon_dungeon_main.drm', 7, 23793, 26, [0x10])
add('(1) matIdx dungeon_main', 'streamgroups/dlc_dungeon_dungeon_main.drm', 7, 23794, 29, [0x10])
add('(1) matIdx dungeon_main', 'streamgroups/dlc_dungeon_dungeon_main.drm', 7, 23795, 32, [0x10])
add('(1) matIdx dungeon_main', 'streamgroups/dlc_dungeon_dungeon_main.drm', 7, 23796, 35, [0x10])
add('(2) tag403 id', 'dlc_dungeonhalla.drm', 7, 20493, 29, [0x6660])
add('(2) tag403 id', 'dlc_dungeonhallb.drm', 7, 20133, 31, [0x5b70])
add('(2) tag403 id', 'dlc_caverns.drm', 7, 20872, 22, [0x54e0])
add('(3) portals', 'dlc_dungeon.drm', 0, 0, 47, [0x114, 0x594, 0x5d4, 0x614, 0x654, 0x694, 0x6d4, 0x714])
add('(3) portals', 'dlc_dungeon.drm', 0, 0, 51, [0x114])
add('(4) model_idx', 'dlc1_uo_dragon_slider.drm', 7, 20457, 2, [0x10a0])
add('(4) flag raft', 'dlc1_uo_raft_bridge.drm', 7, 20765, 3, [0x414])
print('| correzione | file | sezione | off | fresh2 (prima) | B8 (atteso) | fresh3 (ottenuto) | uguale a B8 |'); print('|---|---|---|---|---|---|---|---|')
for r in rows: print('| ' + ' | '.join(str(x) for x in r) + ' |')
print('ALL EQUAL B8:', all(r[-1] for r in rows), 'words', len(rows))
